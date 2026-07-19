# Tesla 온보딩 — Vehicle Command Proxy 설명 + 첫 실차주 E2E 테스트 절차

> 작성: 2026-06-23 (Vehicle Command Proxy 활성화 직후). 대상 = 운영자/개발자.
> 관련 코드: `backend/app/routers/onboard.py`·`settings.py`·`well_known.py`, `docker/docker-compose.yml`·`deploy.sh`, `infra/envs/dev/main.tf`.
> 관련 문서: `AWS_SETUP_GUIDE_BEGINNER.md` §9.5/§9.5.2, `ARCHITECTURE.md` §5/§6.

---

# Part 1 — Vehicle Command Proxy, 쉽게 이해하기

## 한 줄 요약
> 차량에 "이 데이터를 이 주소로 보내라"는 설정(`fleet_telemetry_config`)을 보낼 때, **Tesla는 그 설정에 우리 파트너 개인키로 "인감 도장"이 찍혀 있길 요구**한다. `tesla-http-proxy`는 그 **도장을 대신 찍어주는 사이드카(대행소)**다.

## 비유 — 인감 도장 대행소
- 우리 앱이 Tesla에 보내는 대부분의 요청(차량 목록 조회 등)은 **그냥 보내면 된다**(일반 우편).
- 그런데 **차량 설정 변경**(`fleet_telemetry_config` 생성)은 위험한 명령이라, Tesla가 **"등록된 파트너 개인키로 서명(인감)된 문서만 받겠다"**고 정해놨다(공식: *"should be called through the Vehicle Command Proxy"*).
- 우리 백엔드가 직접 서명하려면 Schnorr(P-256) 같은 특수 암호를 구현해야 해서 비권장 → **Tesla가 만든 공식 프록시(`tesla/vehicle-command` 이미지)**에게 "이 요청에 도장 찍어서 Tesla로 전달해줘"라고 맡긴다.

## 왜 필요했나 (해결한 문제 = #3 HIGH)
- 우리 앱은 `.well-known/.../public-key.pem` 으로 **공개키를 등록하는 방식**의 앱이다.
- 이런 앱은 `fleet_telemetry_config`를 **반드시 서명**해서 보내야 한다(미서명 직접 POST는 옛날 CSR 등록 앱만 허용).
- 서명 없이 보내면 → 현행 펌웨어(2024.26+) 차량에서 **설정이 적용 안 되거나 거부**됨.
- 차주 0건이라 그동안 잠복해 있었고, 이번에 **첫 실차주가 들어오기 전에 정식 경로(프록시 서명)로 활성화**했다.

## 요청 흐름 (활성화 후)

```
[차주 온보딩: 차량 등록]
        │
        ▼
  우리 backend (onboard.register)
        │   ① config push만 프록시로 (다른 Tesla 호출은 직접)
        │   Authorization: Bearer <차주 access_token>  (토큰은 backend가 실음)
        ▼
  tesla-http-proxy  (사이드카, 같은 EC2 안)
        │   ② 파트너 개인키로 fleet_telemetry_config 서명 (인감)
        ▼
  Tesla Fleet API  (fleet-api.prd.na...)
        │   ③ 서명 검증 OK → 차량에 설정 전달
        ▼
  차주 차량 → mTLS로 텔레메트리 전송 → 우리 telemetry EC2 → Kafka → DB
```

- **프록시를 거치는 호출은 딱 3곳**: `onboard.register`(차량 등록) · `settings.validate`(신호 dry-validation) · `settings.repush`(전체 재전송). 나머지 Fleet API 호출(products·fleet_status 등)은 **직접** 간다.
- 토큰 인증은 **여전히 backend가** 담당(차주 Bearer 토큰을 프록시에 실어 보냄). 프록시는 **서명만** 추가하는 passthrough.

## 우리 구성에서 핵심 포인트
| 항목 | 내용 | 이유 |
|---|---|---|
| **토글** | `.env` `TESLA_USE_COMMAND_PROXY=1` (라이브 ON) | gradual 패턴 — 0이면 직접 호출(롤백) |
| **게이트** | `COMPOSE_PROFILES=command-proxy` 일 때만 컨테이너 기동 | 미활성 시 5컨테이너, 활성 시 6컨테이너 |
| **네트워크 격리** | 전용 `command-proxy-net`, **backend만 join** | frontend/nginx/consumer는 프록시 도달 불가(인터넷 비노출) |
| **TLS** | backend↔proxy 는 self-signed TLS (CA를 backend가 검증) | 같은 EC2 내부 통신이라 self-signed로 충분 |
| **이미지 핀** | `tesla/vehicle-command@sha256:e8adac67…` (digest) | 재배포 시 동작 조용한 변동 차단 |

## 활성화하면서 겪은 함정 3가지 (다음에 동형 작업 시 참고)
1. **compose `command`는 flags-only** — 이미지 ENTRYPOINT가 이미 `tesla-http-proxy`라, command에 바이너리명을 또 쓰면 중복 실행 크래시. `-tls-key … -port 4443` 플래그만.
2. **이미지가 non-root UID 65532(distroless)** — root 소유 0600 키 파일을 못 읽어 crash-loop. deploy.sh가 `chown -R 65532 proxy-config` 수행.
3. **EC2 IAM은 명시 ARN 허용목록** — 개인키 secret 읽기 권한을 `main.tf`의 ARN 목록에 **명시 추가**해야 함(와일드카드 아님). 누락 시 deploy가 개인키 fetch에서 AccessDenied.

> **하드닝(0d3f350)**: transient secret 실패가 토글을 0으로 영구 덮어쓰던 무음 회귀(#3 HIGH로 조용히 복귀) 차단 — `_PROXY_ACTIVE`(이번 배포 한정)와 운영자 토글을 분리. secret 회복 시 다음 배포에 자동 재활성.

---

# Part 2 — 첫 실차주 E2E 테스트 절차

> 목표: 실제 Tesla 차량을 가진 차주 1명으로 **로그인 → 페어링 → 등록(프록시 서명) → 텔레메트리 수집**까지 정식 경로가 끝까지 동작함을 확인.
> 차주 0건이라 아직 미발현 — 이 절차가 첫 실증이 된다.

## 사전 점검 (운영자, 차주 부르기 전)

```bash
AWS="aws --profile teslafleet --region ap-northeast-2"
APP=i-0c939b19727922d40

# 1) well-known 200 (페어링 선행 조건) — 404면 키 secret/배포 문제
curl -s -o /dev/null -w "%{http_code}\n" \
  https://sphere.tesla.modapl.dev/.well-known/appspecific/com.tesla.3p.public-key.pem   # 기대 200

# 2) 프록시 컨테이너 안정 + 활성 토글
$AWS ssm send-command --instance-ids $APP --document-name AWS-RunShellScript \
  --parameters 'commands=["sudo docker inspect docker-tesla-http-proxy-1 --format \"State={{.State.Status}} Restart={{.RestartCount}}\"","grep -E \"TESLA_USE_COMMAND_PROXY|COMPOSE_PROFILES\" /opt/teslafleet/docker/.env"]' \
  --query Command.CommandId --output text
#   기대: State=running Restart=0 / TESLA_USE_COMMAND_PROXY=1 / COMPOSE_PROFILES=command-proxy

# 3) 파트너 도메인이 Tesla에 등록돼 있는지 (페어링 deeplink 전제)
#    → register_partner_account.py 재실행 또는 public_key GET 으로 확인(§9.5.1)
```
**체크리스트**: well-known 200 · proxy running Restart=0 · 토글 1 · 파트너 도메인 등록됨.

## 준비물 (차주)
- 실제 Tesla 차량(2018+ 하드웨어, 펌웨어 2024.26+ 권장 — streaming telemetry 지원).
- 차량과 연동된 Tesla 계정 + **Tesla 모바일 앱**(가상키 페어링에 필수).
- 차량이 **온라인(online)** 상태면 즉시 적용, asleep이면 다음 wake 시 적용.

---

## Step 1 — 로그인 / OAuth
1. 차주가 브라우저에서 **`https://sphere.tesla.modapl.dev/onboard`** 접속 → "시작" 버튼.
2. `GET /api/v1/auth/login` → Tesla `auth.tesla.com` authorize로 redirect.
3. 차주가 Tesla 계정 로그인 + 권한 동의(scope 5종).
4. callback → 토큰을 **`fleet-auth.prd.vn.cloud.tesla.com`** 에서 교환 → `vehicle_owner_tokens`에 KMS 봉투암호화 저장 + **세션쿠키(`tf_onboard_owner`)** 발급 → `/onboard/vehicles`로 이동.

**검증**: `/onboard/vehicles` 화면 진입 성공(에러 없이). 서버 로그에 `admin bootstrap` 류 에러 없음.
**실패 시**: 4xx면 OAuth host(token=fleet-auth) 1순위 의심 → `oauth_token_host_pending` 참조.

## Step 2 — 차량 목록 + 페어링 상태 확인
1. `/onboard/vehicles` 가 `GET /api/v1/onboard/products` 호출 → 차주 차량 목록(VIN·이름·online 여부) + 페어링 상태 표시.
2. 응답에 `fleet_status_available`·차량별 `paired`(true/false/null) + `pairing_url` 포함.

**검증**: 차주 실차량이 목록에 보임. `paired=false`면 Step 3 필요, `paired=true`면 Step 4로.

## Step 3 — 가상 키 페어링 (paired=false일 때)
1. 차주가 **Tesla 모바일 앱이 깔린 휴대폰**에서 페어링 deeplink 열기:
   **`https://tesla.com/_ak/sphere.tesla.modapl.dev`**
   (화면의 "페어링" 버튼/QR로 안내됨.)
2. Tesla 앱이 우리 `.well-known` 공개키를 fetch → 차량에 우리 앱의 virtual key 추가.
3. 페어링 완료 후 `/onboard/vehicles` 새로고침 → 해당 차량 `paired=true` 확인.

**실패 시**: deeplink가 "domain not registered" → 파트너 재등록(§9.5.1). well-known 404 → 사전 점검 1로 복귀.

## Step 4 — 차량 등록 (⭐ 프록시 서명 핵심 구간)
1. 차주가 차량 선택 후 "등록" → `POST /api/v1/onboard/register/{vin}`.
2. backend가 `fleet_telemetry_config`를 **프록시 경유로 서명**해 Tesla에 전송.
3. 응답 `status`별 의미:

| status | 의미 | 다음 행동 |
|---|---|---|
| `ok` (`synced` 필드 포함) | **설정 전송 성공** — 차량 온라인이면 즉시, 아니면 다음 연결 시 적용 | Step 5로 |
| `needs_pairing` (412 / `missing_key`) | 가상키 페어링 누락 | Step 3 재수행 후 재등록 |
| `limit_reached` | 차량이 third-party config 슬롯 한계(최대 5개) | 다른 앱 등록 해제 후 재시도 |
| `error` (`unsupported_firmware`/`hardware`) | 펌웨어/HW 미지원 | 차량 업데이트 또는 수집 불가 |

**⭐ 프록시 서명 검증 (운영자)**: register 직후 서버 로그 + 프록시 안정 확인.
```bash
# 프록시가 서명 요청을 처리했는지 + 여전히 안정한지
$AWS ssm send-command --instance-ids $APP --document-name AWS-RunShellScript \
  --parameters 'commands=["sudo docker logs --tail 30 docker-tesla-http-proxy-1 2>&1","sudo docker inspect docker-tesla-http-proxy-1 --format \"Restart={{.RestartCount}}\""]' \
  --query Command.CommandId --output text
#   기대: 프록시 로그에 서명/전달 흔적, Restart 증가 없음(크래시 안 함)
```
**Tesla 측 최종 확인(선택)**: 차주 토큰으로 `GET /api/1/vehicles/{vin}/fleet_telemetry_config` → 응답 `synced=true`(차량이 설정을 채택)면 완전 성공. (create 응답의 synced는 항상 null — 진짜 동기화 여부는 이 GET으로만 확인됨.)

## Step 5 — 텔레메트리 수집 확인 (최종)
차량이 온라인이 되면 mTLS로 데이터를 보내기 시작 → telemetry EC2 → Kafka → consumer → DB.

```bash
# (a) 메인 대시보드 / 차량 목록에 해당 차량이 data_source=live 로 등장 + event_count 증가
#     https://sphere.tesla.modapl.dev/  또는 /vehicles  (관리자 로그인)

# (b) 데이터 현황 — Kafka lag·적재 추이로 유입 확인
#     https://sphere.tesla.modapl.dev/admin/data-status  (KafkaLag·DataQuality 카드)

# (c) DB 직접 확인 (BeeKeeper / psql) — 해당 VIN의 최근 이벤트
#     SELECT vin, data_source, event_count, last_event_at
#       FROM vehicles WHERE vin = '<차주 VIN>';
#     last_event_at 이 현재 시각 근처로 갱신되면 수집 정상.
```

**성공 기준(E2E PASS)**:
1. register `status=ok` 반환 + 프록시 Restart 증가 없음
2. (선택) Tesla GET `fleet_telemetry_config` `synced=true`
3. 차량이 `/vehicles`에 **live**로 등장, `event_count`·`last_event_at` 증가
4. `/admin/data-status`에서 Kafka 유입·적재 확인

---

## 트러블슈팅 빠른 표
| 증상 | 원인 후보 | 조치 |
|---|---|---|
| well-known 404 | 파트너 키 secret 부재/배포 안 됨 | `setup_partner_keys.sh` + 재배포(§9.5) |
| 페어링 deeplink "domain not registered" | 파트너 도메인 미등록 | `register_partner_account.py`(§9.5.1) |
| register `needs_pairing` | 차량 virtual key 누락 | Step 3 페어링 후 재등록 |
| register가 **미서명 거부**(과거 #3) 증상 | 토글이 0으로 회귀 / 프록시 미기동 | `.env` 토글·`COMPOSE_PROFILES`·proxy running 확인 |
| 프록시 crash-loop | UID 권한(chown 65532)·command flags·키 파일 | deploy.sh 로그·`docker logs tesla-http-proxy` |
| register ok인데 데이터 안 옴 | 차량 asleep / mTLS 인증서 / 펌웨어 | 차량 wake 후 대기, telemetry EC2·CA 점검 |

## 롤백
프록시 경유에 문제가 생기면 즉시 직접 호출로 복귀:
```bash
# EC2 docker/.env 에서 TESLA_USE_COMMAND_PROXY=0 으로 변경 후 재배포
#   → 프록시 컨테이너 미기동, config push는 backend가 직접(미서명) 전송
#   ⚠️ 단, 미서명은 #3 HIGH 재발(현행 펌웨어 거부 가능) — 임시 진단용으로만.
```

---

> **현재 상태(2026-06-23)**: 위 사전 점검 1~3 모두 PASS(well-known 200·proxy running Restart=0·토글 1·파트너 재등록 완료). Step 1~5는 **첫 실차주가 들어오면 실증** 예정.
