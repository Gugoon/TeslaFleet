# Silver — telemetry_signals (Bronze valid → 정규화 long)

> **범위**: contract **valid**(pass) Bronze 행의 `raw_payload`(Tesla V JSON)를 신호별 **long(tidy)** 으로
> 평탄화 + value oneof 7종 타입 분해 + 자연키 dedup(2026-06-10: isResend 필터 제거 — 아래 §3-4). Iceberg, **Glue 단독 생성·관리**
> (Athena DDL+Spark write 혼용 금지 — Bronze result S3 404 사고 교훈, BRONZE_CONTRACT_VALIDATION_DESIGN 참고).

## 1. 목적
- `valid_v`(검증 통과)만 Silver로 → **신뢰 경계** 유지(quarantine 제외).
- `raw_payload` → long: **신호 1개 = 1행**. 신호 종류가 많고(PackVoltage/Location/…) sparse(delta-encoded)라 wide보다 long이 적합.
- 타입 정규화(string 보존 + 숫자 통합 + lat/lon) + dedup. **carry-forward 합성·집계는 Gold/쿼리 시점**.
- PG `telemetry_events`(운영 carry-forward wide, RDS, 대시보드/API)와 **별개**: Silver = lakehouse 분석(Athena, 히스토리, 재처리 source).

## 2. 스키마 (`teslafleet_silver_dev.telemetry_signals`, Iceberg, partition `day(event_time)`)
| 컬럼 | 타입 | 설명 |
|---|---|---|
| event_id | string | Bronze lineage |
| source | string | tesla_fleet_v |
| vin | string | 차량 |
| event_time | timestamp | createdAt 파싱 |
| signal_key | string | 예: PackVoltage / Location |
| signal_value | string | **원시 값 보존**(모든 타입 string화) |
| value_type | string | string/int/long/float/double/boolean/location/unknown (7종 외 oneof는 unknown) |
| num_value | double | 숫자 타입 통합 — **doubleValue/floatValue/longValue/intValue만** 채움(`bronze_to_silver_job.py` coalesce). ⚠️ Tesla가 숫자를 **stringValue로 보내는 신호**(BrickVoltage*·DiTorque*·ACChargingEnergyIn·내비 ETA 등 다수)는 `value_type=string`·`num_value=NULL`이며 값은 `signal_value`에만 보존 → 숫자 분석 시 `coalesce(num_value, try_cast(signal_value AS double))` 필요(데이터 레이크 분석 `_NUM_EXPR`와 동일) |
| lat, lon | double | locationValue 분해 |
| raw_topic / raw_partition / raw_offset | string/int/bigint | Bronze lineage |
| silver_job_id | string | Glue JobRunId |
| silver_loaded_at | timestamp | 적재 시각 |
| ingested_at | timestamp | Bronze 적재 시각 — **GL-2 증분 워터마크 산출원**(`max(ingested_at)`)·lineage(§4.0). 구버전 Silver는 `ALTER ADD COLUMN`으로 추가 |

> **SIM 제외 정책(audit MED, 2026-06-04)**: s3_archiver는 SIM 메시지의 raw S3 archive만 skip하고
> Bronze envelope publish는 무조건 수행하므로(`source=tesla_fleet_v`) **SIM-\* VIN 메시지도 Bronze→
> contract validation pass→Silver로 유입**된다. Silver는 실차량 분석 source(Athena/히스토리/재처리)라
> 시뮬 데이터가 섞이면 안 됨 → job이 `from_json` 직후 곧바로 **`vin LIKE 'SIM-%'` 행을 제외**
> (`bronze_to_silver_job.py`, explode/invalid 필터 이전 — 2026-06-10 isResend dedup 단계 제거로 위치 갱신). PG 운영 store는 `is_simulated`/`data_source`로 분리하지만 Silver엔 구분 컬럼이
> 없어 prefix 차단을 채택(null vin은 보존). v2에서 `is_sim` 컬럼 추가 검토 가능.

## 3. 적재 (`glue/bronze_to_silver_job.py`, Glue Spark)
1. `telemetry_raw`(**`source=tesla_fleet_v`만**; alerts/connectivity/errors는 `data[]`가 없어 explode 시 빈 행/오파싱 → join 전에 제거) ∩ `validation_result`(current 최신, status=`pass`) **inner join** → valid 행 (+ `vin LIKE 'SIM-%'` 제외)
2. `from_json(raw_payload, PAYLOAD_SCHEMA)` + `explode(data)` → 신호별 row
3. value oneof 7종 → `value_type` + `signal_value`(string) + `num_value`/`lat`/`lon`. 7종 외 enum `*Value`(tireLocationValue 등)는 `value_type=unknown`이나 generic map 파스로 원본 value JSON을 `signal_value`에 무손실 보존(단기완화, v2 스키마에서 StructField 추가해 분해 확장)
4. ~~dedup: `isResend != true`~~ → **2026-06-10 제거**: isResend=true는 연결 단절 중 차량이 버퍼한 데이터의 재전달로 **재전송이 유일본**인 경우가 일반적 — drop하면 단절 구간이 Silver에서 영구 누락(PG 운영 store는 필터 안 함). 진짜 중복은 §4의 콘텐츠 자연키 dedup이 흡수. 같은 단계에서 `{"invalid": true}` 신호-부재 마커는 제외(운영 파서와 동일 semantics — 이전엔 value_type=unknown 행으로 적재돼 행 인플레이션). `longValue`는 StringType 파스(proto3 JSON은 int64를 string으로 직렬화 — LongType이면 Spark 3.3에서 메시지 전체 무흔적 유실, num_value cast는 동일)
5. **증분**: 이미 Silver에 있는 콘텐츠 자연키 `(vin, event_time, raw_topic, signal_key)` 제외(left-anti) — Silver 미적재분만. `event_id`는 s3_archiver의 archive 시점 uuid4라 replay 재적재마다 달라져 멱등하지 않으므로 키에서 제외(lineage 컬럼으로만 보존)
6. write: **Glue 단독** `create`(첫 run) / `append`(이후), partition `day(event_time)`
   - **테이블 속성(개선감사 2026-06-16)**: `write.target-file-size-bytes=128MB` + `write.parquet.compression-codec=zstd` — 파티션 내 작은 파일 난립 억제(스캔 효율↑·저장량↓). create는 `tableProperty()`, 기존 테이블은 누락 시 1회 `ALTER SET TBLPROPERTIES`(매 run SET=metadata 증식 방지). 미래 write/compaction에만 적용→기존 파일 무손상·점진. sort order는 fanout write 충돌 회피로 미적용(OPTIMIZE 시 별도 검토).

## 4. 증분/멱등
- 콘텐츠 자연키 `(vin, event_time, raw_topic, signal_key)` 기준 left-anti(`event_id`는 replay마다 달라지는 uuid4라 키 제외, lineage로만 보존).
- result의 `current pass`만 대상 → quarantine/pending 자동 제외.

### 4.0 ✅ GL-2 워터마크 구현 (증분 — 2026-06-16)
> §4.1의 raw_offset 설계 대신 **ingested_at 워터마크**로 구현. Bronze raw는 `day(ingested_at)` 파티션(connector)이라 ingested_at이 자연 watermark.
- **Bronze 읽기 프루닝**: `raw.filter(ingested_at >= max(silver.ingested_at) - margin(기본 96h))` — 풀스캔→유입량으로 bound(day(ingested_at) 파티션 프루닝). margin이 validation 지연·경계분 흡수. (2026-06-17 **48h→96h 상향**: validation deterministic-read margin 72h + 24h 버퍼로 48~72h 경계 error→pass flip을 확실히 흡수. 비용=재읽기 윈도우 2배(유입량 비례), dedup 멱등이라 Silver 결과 불변.)
- **done(left-anti 우변) 프루닝**: sig의 `event_time [min,max]` 범위로 한정. 조인 키에 event_time이 있어 그 범위 밖 Silver 행은 매치 불가 → **결과 100% 불변(안전)**. Silver `day(event_time)` 파티션 프루닝 효과.
- **B#5(2026-06-16): validation result(`res`) semi-join 선필터** — `current pass` 산출용 `row_number()` 윈도우가 result 전체를 셔플/정렬해 result 누적(Bronze 비례)에 비례해 비용 무한 증가했음. 최종 `valid = raw INNER JOIN pass_keys`라 **bound된 raw의 (topic,partition,offset) 키로 `res`를 left-semi 선필터**한 뒤 윈도우를 돌린다(GL-2 done 프루닝과 동일 안전 논거 — 조인 키 기준, raw에 없는 offset은 어차피 inner join에서 탈락 → **결과 불변**; semi-join은 매칭 offset의 모든 attempt 행을 보존해 latest-attempt 선택 정확). 워터마크 null(풀 backfill)이면 raw=전체라 선필터 no-op → 그 경로는 건너뜀(불필요한 full-Bronze distinct/이중스캔 회피).
- **ingested_at을 Silver에 보존**(워터마크 산출원). 구버전 Silver는 멱등 `ALTER TABLE ADD COLUMN ingested_at`으로 호환(create 경로는 자동).
- **안전장치**: 워터마크 null(첫 run·Silver/컬럼 부재) → 전체 읽기=풀 backfill(self-heal, 기존 동작). replay는 ingested_at이 최신이라 윈도우 안 → 누락 없음.
- ⚠️ **late error→pass flip 한계(2026-06-17 명시)**: margin(96h)은 **transient** error flip만 보장한다. validation의 'error'는 except 캐치올(일시 런타임 오류)이라 보통 1~2회 시간당 run 내 pass로 재검증되고 그 행의 ingested_at은 최신이라 윈도우 안에 든다. 그러나 validation은 `effective=min(cutoff, err_min)`(현재 error-only offset의 min ingested_at)으로 재검증 윈도우를 **무제한** 확장하는 반면 Silver read는 ingested_at 96h cutoff로만 bound된다 → 어떤 offset이 **>96h 동안 error로 머물다**(예: 며칠 지속된 validator 버그) 연속 유입 중 pass로 flip되면 Silver는 그 행을 영구 누락(분석층<운영 PG)할 수 있다. 단 (a)운영상 가시적(다일 validator 장애)이고 (b)**Silver 비우면 풀 backfill self-heal로 복구** 가능. 완전 대칭 수정(Silver를 ingested_at이 아닌 validation result의 `validated_at` 워터마크 기반으로)은 B#5가 제거한 full-result O(Silver) 스캔을 재도입하므로 라이브 검증 후 별도 결정(현 단계 보류).
- ✅ **라이브 검증 완료(2026-06-16)**: 첫 run(풀 backfill, watermark=none) SUCCEEDED·schema evolution 정상 / 증분 run 로그 `watermark: max_ingested_at=...` 전환·**ExecSec 1124s→348s(3.2배↓)** / **무손실** Silver 51.6M 신호·13.61M distinct 이벤트 불변·**≈ PG 13.53M event**·margin left-anti 0 append(멱등). 배포=terraform apply(스크립트 S3 재업로드, drift 0).

### 4.1 ⏳ (대체됨) 초기 설계 — raw_offset watermark (§4.0 ingested_at로 구현 / 2026-06-10 audit)
> **현 상태는 정상 동작**한다. 이건 *비용* 개선이며 Silver 증가에 비례해 ExecutionTime(=Glue 과금단위)이
> 선형 creep하는 것을 막기 위함. 1시간 주기 토글 OFF 운영이라 긴급하지 않아 **별도 검증된 Glue 1회 run으로
> row count 대조 후** 적용. blind 적용 금지(Spark job은 로컬 테스트 불가 → 미묘한 무손실 위반 위험).

**문제**: 현재 job은 매 run `telemetry_raw` 전체 ∩ `validation_result` 전체를 재파싱하고, `done =
spark.table(silver).distinct()`로 **Silver 전체를 스캔·셔플**한다. left-anti는 *write*만 증분이고 *read*는
전량이라, 단순 event_time 범위 필터는 no-op(replay는 event_time이 과거라 범위 밖 → 오히려 누락). 효과적
최적화는 **유입(raw) 측 선게이팅**이 선행되어야 한다.

**안전 설계**(구현 시 이대로):
1. `wm = Silver.groupBy(raw_topic, raw_partition).agg(max(raw_offset))` — partition별 high-water mark
   (Iceberg per-file 통계로 단일 컬럼이라 4-컬럼 distinct보다 저렴).
2. `todo_new = raw[offset > wm[partition]] ∩ pass_keys` — **신규 데이터는 anti-join 불필요**
   (offset > Silver max ⇒ 확실히 미적재). replay는 s3_archiver 재발행으로 **새 Kafka offset**을 받아
   watermark 초과 → 통과·재처리(안전).
3. ⚠️ **재검증 rescue 필수**: error→pass 재검증(`validation_attempt > 1`) 행은 offset이 watermark
   *아래*라 (2)에서 누락된다. `cur`/`pass_keys`는 이미 result 전체를 보므로 `attempt > 1`만 추가 게이트해
   `todo_reval = raw ∩ pass_keys[attempt>1]`(드물어 broadcast)로 **offset 무관 구제**. 단 `todo_reval`은
   이미 Silver에 있을 수 있으므로 **이 부분만** left-anti(또는 Iceberg MERGE) 유지.
4. `todo = (todo_new ∪ todo_reval)` 후 기존 `dropDuplicates` 백스톱.

**검증 게이트**(적용 전 필수): 토글 OFF 상태에서 신규 job을 1회 수동 실행 → Silver row count가 기존
로직과 동일한지(±0) Athena로 대조. 특히 error 상태 offset을 인위로 만들어 재검증 rescue가 동작하는지 확인.
이 게이트 없이는 적용 금지.

## 5. 단계
1. ✅ 설계 + job (`glue/bronze_to_silver_job.py`)
2. ✅ terraform 적용 — `infra/modules/bronze_validation/silver.tf`: `teslafleet_silver_dev` Glue DB + Glue job `teslafleet-dev-bronze-to-silver` + IAM(bronze read + silver write) + EventBridge Scheduler(`cron(30 * * * ? *)` Asia/Seoul — **매시 :30, 1시간 주기**, validation 매시 :00과 발화 분 비겹침, `bronze_to_silver_schedule_enabled=true` 최초 생성 시 적용·이후 state는 `ignore_changes`로 런타임 토글 보존). fanout은 terraform `--conf`가 아니라 **job 스크립트의 write option**으로 적용(아래 fanout 교훈)
   - **비용 최적화(2026-06-08)**: Silver 실행 실측 ~712s(~11.9분) — 12분 주기 시 사실상 24/7이라 Glue 비용 최대였음. **1시간 주기로 완화**(~81%↓) + '데이터 현황'(/admin/data-status) **ON/OFF 토글**(안 쓸 땐 과금 ~0). 상세 [[lakehouse_cost_toggle]].
3. ✅ 첫 run(create) + Athena 검증 완료 — 2026-06-02 (`telemetry_signals` **2,144,500 long rows** / 4 vin / 203 signal_key, value_type=string·location·double·int·boolean, location는 lat/lon 분해. value_type=unknown 1.1%는 향후 oneof 보강 대상). **이후 전체 backfill 후 라이브 스냅샷(파이프라인 OFF·2026-07 실측) ≈ 51.6M signal rows / 13.6M 이벤트 / 실차 7 VIN / 253 signal_key** — 데이터 레이크 분석 화면(`/admin/data-lake`)·API_REFERENCE 기준값
4. (향후) Gold: carry-forward 합성 wide / 집계

> ⚠️ **fanout 교훈**: `day(event_time)` partition write 시 입력이 partition별로 clustering 안 되면 `records not clustered by partition` 으로 job abort. 해결은 **Iceberg write option** `.option("fanout-enabled", "true")` (`glue/bronze_to_silver_job.py`의 create·append 양 write 경로 `writeTo(silver_fqn).option("fanout-enabled","true")`) — `spark.sql.iceberg.write.fanout.enabled` 같은 **spark conf로는 적용되지 않음**(잘못된 키 → ClusteredWriter 유지, `silver.tf` fanout `--conf` 주석 참조). validation의 result 테이블은 partition 없어 무관.
