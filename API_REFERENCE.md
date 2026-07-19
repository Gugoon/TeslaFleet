# TeslaFleet Backend API Reference

> **버전**: 0.1.0 · 기준: **v1.9.0** (2026-07-03, alembic head=**0050** 무변경 — ⭐**데이터 레이크 분석 신설**: S3 Silver/Bronze(Iceberg)를 Athena로 조회하는 admin 전용 정적 히스토리 화면(`/admin/data-lake`)+백엔드 5 엔드포인트(`admin/datalake/*`). 직전 v1.8.2=MFA to_thread·verify-otp 미분배 403·타임아웃/lock_timeout 하드닝) · 베이스 코드: `backend/app/`
>
> 이 문서는 `backend/app/routers/*.py` + `backend/app/schemas.py` + `backend/app/models.py` 소스를 옮긴 **수기 관리** 사양입니다. 운영은 보안상 Swagger UI(`/docs`) 비공개(`ENABLE_OPENAPI=0` + nginx 미라우팅). 코드 변경 시 본 문서를 같은 commit에서 동기화하는 것이 규칙입니다.
>
> 📖 **DB 테이블 스키마 + 관계도**: [`docs/DB_SCHEMA.md`](DB_SCHEMA.md) — 15 테이블 + Alembic 0050 + ERD(Mermaid) + 인덱스 정책. 마이그 추가 시 동기화 필수.
>
> 💡 **전체 endpoint를 한눈에**: [3.0 빠른 참조](#30-빠른-참조-전체-103개)

## 목차

- [1. 개요](#1-개요)
- [2. 공통 사양](#2-공통-사양) · [2.6 curl 빠른 테스트](#26-curl-빠른-테스트-사용법)
- [3. 엔드포인트](#3-엔드포인트)
  - [**3.0 빠른 참조 (전체 103개)**](#30-빠른-참조-전체-103개) ⭐
  - [**3.0.1 curl 복붙 모음**](#301-curl-복붙-모음) ⭐
  - [3.1 헬스체크 (`/health`)](#31-헬스체크-health)
  - [3.2 인증 (`/api/v1/auth`)](#32-인증-apiv1auth)
  - [3.3 온보딩 (`/api/v1/onboard`)](#33-온보딩-apiv1onboard)
  - [3.4 차량 (`/api/v1/vehicles`)](#34-차량-apiv1vehicles)
  - [3.5 텔레메트리 (`/api/v1/telemetry`)](#35-텔레메트리-apiv1telemetry)
  - [3.6 설정 (`/api/v1/settings`)](#36-설정-apiv1settings)
  - [3.7 시뮬레이터 (`/api/v1/admin/sim`)](#37-시뮬레이터-apiv1adminsim)
  - [3.8 Seed 관리 (`/api/v1/admin/seed`)](#38-seed-관리-apiv1adminseed--alembic-001900200022)
- [4. 데이터 모델](#4-데이터-모델)
- [5. 에러 코드 표](#5-에러-코드-표)
- [6. Swagger UI / OpenAPI](#6-swagger-ui--openapi)
- [알려진 이슈](#알려진-이슈)
- [변경 이력](#변경-이력)

---

## 1. 개요

| 항목 | 값 |
|---|---|
| Title | `TeslaFleet API` |
| Version | `0.1.0` |
| API prefix | `/api/v1` (`health` 제외) |
| 운영 base URL | `https://sphere.tesla.modapl.dev` |
| 온보딩 base URL | `https://onboard.tesla.modapl.dev` (`/api/v1/onboard/*` 호출 시도 가능 — nginx가 같은 backend로 proxy) |
| Content-Type (응답) | `application/json; charset=utf-8` |
| 인코딩 | UTF-8 — 한국어 문자열은 raw, 이스케이프 안 함 (`utils/responses.json_utf8`) |

`api_v1_prefix`는 `backend/app/config.py`의 `Settings.api_v1_prefix`(`"/api/v1"`) 상수입니다.

## 2. 공통 사양

### 2.1 인증

> **v1.7.0 (Alembic 0041)**: nginx Basic auth **제거** → **계정 세션 로그인**으로 전환.
> role: **admin**(전 메뉴·전 데이터) / **manager**(고객사 소속 — 메인현황·차량정보만, 자기 고객사 데이터만).
> 세션 쿠키 `__Host-tf_account`(v1.7.1 — `__Host-` prefix: Secure + Path=/ + Domain 없음 강제, HttpOnly + SameSite=Lax, 30일) — DB 서버측 세션(`account_sessions`, sha256 해시 저장)이라 비번 리셋/분배 변경 시 **즉시 revoke**.
> `ACCOUNT_AUTH_ENFORCE=0`(기본, 테스트/로컬 dev)이면 require_account no-op(legacy 무인증) — deploy.sh가 1로 설정.

| Router | 보호 방식 |
|---|---|
| `health.*` / `well-known.*` | 없음 (공개) |
| `auth.*` (Tesla OAuth) | OAuth state cookie (`tesla_oauth_state`, 10분 만료, Domain=.tesla.modapl.dev, HttpOnly + Secure + SameSite=Lax) — `/callback`에서 검증 |
| `auth/account.*` (계정 로그인) | 공개(로그인 전 호출) — nginx `^/api/v1/auth/` **auth_zone rate limit(10 r/s)** 이 brute-force 완화. `/password`는 세션 필수 |
| `onboard.*` | OAuth callback이 발급한 **HMAC 서명 세션 쿠키**(`tf_onboard_owner`, domain=`.tesla.modapl.dev`, 30일, HttpOnly + Secure + SameSite=Lax)로 인증 — owner_id 쿼리는 **무시**(IDOR 방지, 2026-06 audit). 쿠키 없음/변조 시 `401 reauth_required` |
| `vehicles.*` / `telemetry.*` / `geocode.*` / `roads.*` / `customers.*` | **`require_account`** — 세션 쿠키(`__Host-tf_account`) 또는 `X-Admin-Key`. 무세션 `401 login_required`. **manager는 `customer_scope`로 자기 고객사 데이터만**(vehicles 목록/통계 필터, 타 고객사 차량·고객사는 404 — 존재 누설 차단) |
| `customers` 변이 5개 + `vehicles/admin/backfill-identity` + `settings.*` / `admin/sim.*` / `admin/seed.*` / `admin/bronze-replay.*` / `admin/kafka-lag.*` / `admin/lakehouse.*` / `admin/datalake.*` / `admin/duplicates.*` / `admin/accounts.*` / `admin/alerts.*` | **`require_admin_account`** — **admin 세션** 또는 `X-Admin-Key`(운영 스크립트/비상용 — `ADMIN_API_KEY` 상수시간 hmac 비교). manager 세션은 `403 admin_required`, 무세션·무키는 `401` |

> ⚠️ **`NEXT_PUBLIC_ADMIN_KEY` 번들 주입은 제거됨**(v1.7.0) — Basic auth 제거로 SPA 번들이 공개되므로 빌드타임 키 인라인은 키 유출. SPA는 세션 쿠키만 사용, `X-Admin-Key`는 서버측 운영 스크립트 전용.

> **수용 리스크(2026-06-12 적대 보안 리뷰 — 사용자 명세 기인, 의도된 동작)**:
> ① signup 409 `email_exists`는 이메일 존재 오라클 — 가입이 email만으로 공개라는 명세상 불가피(로그인은 더미 검증으로 타이밍 균등화·uniform 401). 스팸 계정은 분배 전 로그인 불가 + Admin 삭제로 정리.
> ② 디폴트 비밀번호 `modapl#123`은 공개 상수 — **고객사 분배가 신뢰 게이트**(Admin이 아는 이메일에만 분배), 분배 후 본인 비번 변경 권장(강제 아님 — 명세).
> ③ `/roads/snap`(유료 Google 프록시)은 분배된 manager도 호출 가능 — 배치 100/요청·25배치 상한 자체 가드로 비용 bounded.

### 2.2 공통 헤더

**요청 (선택)**
- `X-Request-ID`: 상류에서 발급한 trace ID. 미지정 시 backend가 `uuid4().hex[:16]`으로 자동 생성.

**응답 (모든 엔드포인트)**
- `X-Request-ID`: 요청 헤더 echo 또는 자동 생성된 ID.
- `Content-Type`: `application/json; charset=utf-8` (JSON 응답인 경우).

### 2.3 CORS

`backend/app/main.py`의 `CORSMiddleware` 설정:
- `allow_origins`: `["https://sphere.tesla.modapl.dev", "https://onboard.tesla.modapl.dev", "http://localhost:3000"]`
  — **prod(`REQUIRE_PROD_CONFIG=1`)에서는 `localhost`/`127.0.0.1` origin 자동 제거**(2026-05-29 audit #17, `config.py` `cors_origins` field_validator). dev/test는 그대로 유지(`CORS_ORIGINS` env override 가능).
- `allow_credentials`: `true`
- `allow_methods`: `*`
- `allow_headers`: `*`

### 2.4 에러 모델

FastAPI 기본 형식 — `HTTPException(status_code, detail)`은 다음 JSON으로 직렬화됩니다.

```json
{ "detail": "사람이 읽을 수 있는 한 줄 메시지" }
```

Pydantic 검증 실패(422) 시 `detail`이 객체 배열로 반환됩니다 (FastAPI 기본):

```json
{
  "detail": [
    { "loc": ["body", "signals", 0, "interval_seconds"], "msg": "ensure this value is greater than or equal to 1", "type": "value_error.number.not_ge" }
  ]
}
```

### 2.5 페이지네이션

별도 페이지네이션 객체 없음. 시계열 endpoint(`/events`, `/alerts`)는 `limit` + `from`/`to`/`last_days`로 범위 제한. 결과는 plain JSON array.

### 2.6 curl 빠른 테스트 사용법

각 endpoint에 복붙 실행 가능한 `curl`을 첨부했습니다. 먼저 base URL을 변수로 export:

```bash
export BASE=https://sphere.tesla.modapl.dev
# 온보딩 도메인 테스트 시: export BASE=https://onboard.tesla.modapl.dev
```

- admin 영역(`settings`/`admin/sim`/`admin/seed`/`admin/bronze-replay`/`admin/kafka-lag`/`admin/lakehouse`/`admin/datalake`/`admin/duplicates`/`admin/accounts`/`admin/alerts`)은 **admin 세션 또는 `X-Admin-Key` 헤더 필요**(`ADMIN_AUTH_ENFORCE=1` 시 불일치/누락 401). curl 시 `-H "X-Admin-Key: <docker/.env의 ADMIN_API_KEY>"` 추가. 2026-06-10: `/customers` **변이 5개**(POST/PATCH/DELETE/vehicles 추가·제거)도 `require_admin_account` 부착 — GET 2개(목록·상세)는 `require_account`. ⚠️v1.7.0부터 `/geocode`·`/roads`·`vehicles`·`telemetry`·`customers`(GET 포함)는 모두 `require_account`(세션 또는 X-Admin-Key, 무세션 401) — 무인증 엔드포인트는 `onboard.*`(HMAC 쿠키)·`auth.*` 뿐. ⚠️`admin/accounts`의 파괴작업(분배/리셋/삭제)은 `require_admin_session`(admin 세션 전용, X-Admin-Key 차단 — `ADMIN_KEY_BLOCK_DANGEROUS=1`)
- `{vehicle_id}` 등 path param은 `GET $BASE/api/v1/vehicles`로 실제 id를 먼저 확보해 치환
- 🟢 = 안전(read-only) · 🔴 = **destructive** (데이터 변경/삭제 — confirm 토큰 포함, 실행 전 반드시 확인)
- 응답 정렬 보기: 뒤에 ` | python3 -m json.tool` 또는 ` | jq` 추가

---

## 3. 엔드포인트

### 3.0 빠른 참조 (전체 103개)

전체 endpoint 한눈에. 상세는 각 섹션(3.1~3.13) 링크.

> **v1.7.0 가드 일괄 변경**: 아래 '가드' 열은 endpoint별 **추가** 가드만 표기.
> 기본 가드(§2.1): 데이터 라우터(vehicles/telemetry/geocode/roads/customers) = `require_account`(세션 또는 X-Admin-Key, manager는 고객사 스코프) ·
> admin 라우터(settings/sim/seed/bronze-replay/kafka-lag/lakehouse/duplicates/accounts + customers 변이) = `require_admin_account`(admin 세션 또는 X-Admin-Key).

#### 헬스체크 · 인증 · 온보딩
| Method | Path | 요약 | 가드 |
|---|---|---|---|
| GET | `/health` | 프로세스 alive (DB 무관) | — |
| GET | `/health/db` | DB 연결 확인 | — |
| GET | `/api/v1/auth/login` | Tesla OAuth 로그인 redirect | — |
| GET | `/api/v1/auth/callback` | OAuth code → 토큰 교환 | — |
| POST | `/api/v1/auth/refresh/{owner_id}` | refresh token으로 access 갱신 | **admin**(v1.7.0 — Basic auth 제거로 공개되던 것 차단, 운영용) |
| POST | `/api/v1/auth/account/signup` | **Manager 가입(email만, 비번 디폴트)** — v1.7.0 | rate limit(auth_zone) |
| POST | `/api/v1/auth/account/login` | 계정 로그인 → 세션 쿠키(MFA 미등록) 또는 `mfa_required`(등록 계정) | rate limit · 미분배 manager 403 |
| POST | `/api/v1/auth/account/login/verify-otp` | **OTP 2단계 검증 → 세션 (v1.7.5)** | rate limit · 챌린지 토큰 · 미분배 manager 403 |
| GET | `/api/v1/auth/account/mfa/setup` | **OTP 등록 시작(QR) (v1.7.5)** | 세션 필수 |
| POST | `/api/v1/auth/account/mfa/enable` | **OTP 등록 확정 + 백업코드 (v1.7.5)** | 세션 필수 |
| POST | `/api/v1/auth/account/mfa/disable` | **본인 OTP 해제(비번 재확인) (v1.7.5)** | 세션 필수 |
| POST | `/api/v1/auth/account/logout` | 세션 삭제 + 쿠키 제거(멱등) | — |
| GET | `/api/v1/auth/account/me` | 현재 세션 계정 + enforce 상태 | — |
| POST | `/api/v1/auth/account/password` | 내 비밀번호 변경(타 세션 revoke) — must_change는 현재 비번 불요 | 세션 필수 |
| GET | `/api/v1/auth/account/sessions` | 내 활성 세션 목록 (v1.7.1) | 세션 필수 |
| DELETE | `/api/v1/auth/account/sessions/{id}` | 특정 세션 원격 로그아웃 (v1.7.1) | 세션 필수 |
| POST | `/api/v1/auth/account/sessions/revoke-others` | 현재 외 전 세션 로그아웃 (v1.7.1) | 세션 필수 |
| GET | `/api/v1/admin/accounts` | 계정 목록(+검색) — 미분배 우선 | admin |
| GET | `/api/v1/admin/accounts/audit` | 보안 감사로그(페이징 limit/offset/total · IP·위치 v1.7.4) (v1.7.1) | admin |
| PUT | `/api/v1/admin/accounts/{id}/customer` | 고객사 분배/해제(세션 revoke) | admin |
| POST | `/api/v1/admin/accounts/{id}/reset-password` | 비번 리셋(디폴트+미분배+revoke) | admin |
| POST | `/api/v1/admin/accounts/{id}/reset-mfa` | **OTP 등록 해제(분실 복구·manager 한정) (v1.7.5)** | admin |
| POST | `/api/v1/admin/accounts/{id}/role` | **역할 승격/강등(manager↔admin·마지막 admin 강등 차단) (v1.7.6)** | admin |
| DELETE | `/api/v1/admin/accounts/{id}` | manager 계정 삭제 | admin |
| GET | `/api/v1/onboard/products` | owner의 Tesla 차량 목록 | 세션 쿠키 (`tf_onboard_owner`) · 401 |
| GET | `/api/v1/onboard/vehicles` | 등록 대상 차량 조회 | 세션 쿠키 (`tf_onboard_owner`) · 401 |
| POST | `/api/v1/onboard/register/{vin}` | fleet_telemetry_config push | 세션 쿠키 (`tf_onboard_owner`) · 401 |

#### 차량 · 텔레메트리
| Method | Path | 요약 | 가드 |
|---|---|---|---|
| GET | `/api/v1/vehicles` | 차량 목록 (`?data_source=` 필터) | — (Alembic 0024 비정규화로 `data_source=seeded` 504 해소) |
| GET | `/api/v1/vehicles/stats` | 차량 수 by source | — |
| GET | `/api/v1/vehicles/{vehicle_id}` | 차량 1대 메타 | — |
| GET | `/api/v1/telemetry/vehicles/{vehicle_id}/events` | 시계열 events (column-aware bucket 다운샘플 + 캐시 TTL data_source별: live 60s / seeded·simulated 600s, v1.6.5 추정 count·행 상한) | `require_account` |
| GET | `/api/v1/telemetry/vehicles/{vehicle_id}/events/count` | 범위 내 event 수(플래너 추정) + 해석된 from/to + row_cap — FE 점진 페이징용 (v1.6.5 신규) | — |
| GET | `/api/v1/telemetry/vehicles/{vehicle_id}/route` | 경로 지도용 — 좌표 원본 row `{ts,lat,lng}` 시간순(row ≤ limit이면 사실상 무샘플링). cap 초과 시 `width_bucket`으로 전체 시간범위를 limit개로 균등 분할 후 각 구간의 첫(가장 오래된) 좌표 1점(SQLite는 `ROW_NUMBER` step), GPS outlier(>270km/h 점프) 필터 → **폴리라인 간소화**(`_simplify_route`: 거리 thinning 3m → Douglas-Peucker ε5m, 직선·노이즈는 접고 커브 꼭짓점 보존 → 도로 정합↑·정점↓). FE는 범위별 limit 차등(>7일 5만 / ≤7일 15만, 넓은 범위 타임아웃 회피)·클라 타임아웃 90s. **무경계/대범위 width_bucket은 `statement_timeout=45s` 초과 시 504 `route_range_too_large`**(events와 대칭, db.t4g.small pool 고갈 방지). (`from`/`to`/`last_days`/`limit≤200000`) | — (신규) |
| GET | `/api/v1/telemetry/vehicles/{vehicle_id}/alerts` | 차량 alerts | — |
| GET | `/api/v1/telemetry/vehicles/{vehicle_id}/latest` | 최신 + carry-forward 머지 (**캐시 TTL data_source별: live 60s / seeded·simulated 600s** — 2026-05-29 audit rank1 무캐시 2000행 JSONB 읽기 제거 + 2026-06-17 events/route와 TTL 통일. `_LATEST_CACHE`) | `require_account` |

#### 차량 심화 분석 (`/api/v1/telemetry`) — v1.7.7 (Alembic 0047/0048/0049/0050)
> 10개 분석 endpoint. 전부 GET·`require_account`(추가 admin 가드 없음·manager는 `customer_scope`로 타 고객사 차량 404)·파라미터 `from`/`to`/`last_days`·결과 LRU 캐시(TTL live 300s / 정적(seeded·simulated) 1800s)·PG는 `SET LOCAL statement_timeout=60s` 초과 시 **504 `range_too_large`**. 상세 [3.5.1 차량 심화 분석](#351-차량-심화-분석-apiv1telemetry--v177).

| Method | Path | 요약 | 가드 |
|---|---|---|---|
| GET | `/api/v1/telemetry/vehicles/{vehicle_id}/charge-sessions` | 충전 세션 분할 + SoC/에너지/전력/AC·DC/위치 + 충전 곡선(#1,#8). ⭐충전 판정 = `charge_state='Charging'` **AND 정지(speed≤1) AND 충전전력>0**(sticky 'Charging' 주행/정차 오염 제외). 세션에 `soc_unreliable`(SoC 비단조 진동 시 true) | `require_account` |
| GET | `/api/v1/telemetry/vehicles/{vehicle_id}/efficiency` | 일별 전비(km/kWh·Wh/km) + 외기온(#2) | `require_account` |
| GET | `/api/v1/telemetry/vehicles/{vehicle_id}/driving-events` | 급가속/급감속/급선회 이벤트(클러스터링) + 운전 점수(#7). `accel_th`/`lat_th`(m/s², 기본 3.0) | `require_account` |
| GET | `/api/v1/telemetry/vehicles/{vehicle_id}/speed-histogram` | 주행 속도 분포 히스토그램 + avg/max/p95(#10) | `require_account` |
| GET | `/api/v1/telemetry/vehicles/{vehicle_id}/places` | 자주 가는 장소(정차 클러스터·~110m 격자)(#9) | `require_account` |
| GET | `/api/v1/telemetry/vehicles/{vehicle_id}/battery-health` | 배터리 건강도/열화(100% 환산 정격거리·에너지 추세)(#11) | `require_account` |
| GET | `/api/v1/telemetry/vehicles/{vehicle_id}/vampire-drain` | 대기 방전(주차 중 SoC 감소율 %/일)(#12) | `require_account` |
| GET | `/api/v1/telemetry/vehicles/{vehicle_id}/activity-calendar` | 일별 운행 거리(GitHub 캘린더 히트맵)(#13) | `require_account` |
| GET | `/api/v1/telemetry/vehicles/{vehicle_id}/utilization` | 가동률(주행/충전/주차 시간 점유) + 커버리지 헬스(수집 공백·채움률). 연속 샘플 간격을 상태 귀속(속도 우선·쿼리 시점 last-value 채움) | `require_account` |
| GET | `/api/v1/telemetry/fleet-baseline` | 시뮬 제외 **전 차량** 전비·운전점수 가중 평균(비교 기준선·**scope 무시 의도적**·`driving.truncated` 포함) | `require_account` |

#### 설정 (`/admin/settings/telemetry`)
| Method | Path | 요약 | 가드 |
|---|---|---|---|
| GET | `/api/v1/settings/known-signals` | Tesla 공식 256 신호 + alias | — |
| GET | `/api/v1/settings/telemetry-config` | 신호 설정 + 비용 + 검증 배지 | — |
| PUT | `/api/v1/settings/telemetry-config` | 신호 설정 저장(replace-set) + 비동기 Tesla 검증 | `confirm=APPLY_CONFIG` |
| POST | `/api/v1/settings/repush-all` | 전체 차량 config 재push | `confirm=REPUSH_ALL` · 5분 cooldown |

#### 시뮬레이터 (`/api/v1/admin/sim`)
| Method | Path | 요약 | 가드 |
|---|---|---|---|
| POST | `/api/v1/admin/sim/start` | sim run 시작 | cap 5 |
| POST | `/api/v1/admin/sim/stop/{run_id}` | sim run 중지 | — |
| GET | `/api/v1/admin/sim/runs` | sim run 목록 | — |
| GET | `/api/v1/admin/sim/runs/{run_id}` | sim run 1개 | — |
| GET | `/api/v1/admin/sim/data-summary` | SIM 데이터 요약 | — |
| DELETE | `/api/v1/admin/sim/vehicles` | SIM 차량 일괄 삭제 | `confirm=DELETE_ALL_SIM` · 5분 cooldown |
| GET | `/api/v1/admin/sim/delete-events` | sim 삭제 audit | — |

#### Seed 관리 (`/api/v1/admin/seed`) — Alembic 0019/0020/0022
| Method | Path | 요약 | 가드 |
|---|---|---|---|
| DELETE | `/api/v1/admin/seed/vehicles/{vehicle_id}` | 차량별 seeded 삭제 (async, 0건=동기) | `confirm=DELETE_SEEDED` · 60s · 409 |
| DELETE | `/api/v1/admin/seed/events?year=&month=` | 월별 seeded 삭제 (async) | `confirm=DELETE_SEEDED_MONTH` · 60s · 409 |
| GET | `/api/v1/admin/seed/delete-jobs/{job_id}` | 삭제 job 진행 상태 polling | — |
| POST | `/api/v1/admin/seed/ingest-one?s3_key=` | 단일 S3 파일 적재 (멱등) | `confirm=SCAN_S3` |
| GET | `/api/v1/admin/seed/monthly-overview` | S3↔DB 월별 비교 (600s 캐시 — 2026-06-01 cold ~13.8s 재발 빈도↓, invalidate 보존) | — |
| GET | `/api/v1/admin/seed/list-month-files?year=&month=` | 월별 file keys | — |
| GET | `/api/v1/admin/seed/imports?limit=&status=` | 적재 audit 이력 | — |
| POST | `/api/v1/admin/seed/reset-in-progress?prefix=` | stuck `in_progress` seed_imports row 일괄 삭제(audit만) | `confirm=RESET_INPROGRESS` · 412 |
| GET | `/api/v1/admin/seed/event-stats?vehicle_id=` | seeded events/alerts 월별 카운트(UI breakdown) | — |

#### Bronze Replay (`/api/v1/admin/bronze-replay`) — Alembic 0035 (v1.5.8)
| Method | Path | 요약 | 가드 |
|---|---|---|---|
| GET | `/api/v1/admin/bronze-replay/preview?prefix=` | S3 prefix 미리보기 (객체 수/byte/sample + **`omitted_topics[]`** — 단일 토픽 prefix가 같은 기간 다른 저장 토픽(tesla_V/tesla_alerts)을 누락 시 경고) | `prefix='topics/'` 필수 |
| POST | `/api/v1/admin/bronze-replay/start` | replay 시작 (background asyncio task). body `allow_partial`(기본 false) — 단일 토픽 prefix가 형제 저장 토픽 누락 시 **409 차단**, `allow_partial=true`로 우회 | 같은 prefix active → 409 · 토픽 누락 → 409 |
| GET | `/api/v1/admin/bronze-replay/list?limit=` | 이력 (최신순) | — |
| GET | `/api/v1/admin/bronze-replay/{id}` | 단건 실시간 status | 404 |
| POST | `/api/v1/admin/bronze-replay/{id}/stop` | running task cancel + 'stopped' | 종료된 row → 409 |
| DELETE | `/api/v1/admin/bronze-replay/{id}` | 이력 row 삭제 (적재 데이터 유지, v1.6.0) | running/pending → 409, 404 |
| GET | `/api/v1/admin/bronze-replay/ingested-vehicles` | 적재 차량 목록 (삭제 UI용, v1.6.1) | — |
| DELETE | `/api/v1/admin/bronze-replay/ingested-vehicles/{id}` | 적재 차량+telemetry/alerts 삭제 (data_source 무관, v1.6.1) | `confirm=DELETE_INGESTED` 412, 404, 409(다른 ingested 삭제 job in_progress) |

#### Kafka lag 모니터 (`/api/v1/admin/kafka-lag`) — v1.5.8
| Method | Path | 요약 | 가드 |
|---|---|---|---|
| GET | `/api/v1/admin/kafka-lag?no_cache=0/1` | 모든 monitor group의 lag (10s TTL cache) | broker 실패 시 stale fallback |

#### Lakehouse 모니터링 (`/api/v1/admin/lakehouse`) — v1.6.x
| Method | Path | 요약 | 가드 |
|---|---|---|---|
| GET | `/api/v1/admin/lakehouse/glue-runs?no_cache=0/1` | 검증/Silver Glue job 최근 실행 현황 (`glue:GetJobRuns`만·**과금0**·30s TTL cache) | — |
| GET | `/api/v1/admin/lakehouse/dq-overview?no_cache=0/1` | Bronze Contract Validation 품질 요약 (Athena: total/pass/fail/error/pass_rate/top_failures, **과금 3중가드**·600s TTL cache) | Athena 실패 시 stale fallback |
| GET | `/api/v1/admin/lakehouse/pipeline-status` | 파이프라인(validation+silver Scheduler) ON/OFF 상태 + 주기 (v1.6.6) | 502(AWS 조회/파싱 실패) |
| POST | `/api/v1/admin/lakehouse/pipeline-toggle?enabled=` | 파이프라인 ON/OFF 토글 — 두 EventBridge Scheduler state 일괄 변경(안 쓸 때 끄면 Glue 과금 ~0, v1.6.6) | 502(부분실패 시 복원) |

#### 데이터 레이크 분석 (`/api/v1/admin/datalake`) — v1.9 ⭐신규

> **admin 전용**(require_admin_account). S3 Silver(`telemetry_signals` — 253 신호·13.6M 이벤트)·Bronze 검증을 Athena로 조회하는 **정적 히스토리** 분석(파이프라인 OFF·실데이터 ~2025-11). 과금 가드: **쿼리 윈도우 스팬 ≤30일 서버 강제**(초과 `422 datalake_range_too_large`, meta만 예외) + workgroup 1GB cutoff + LRU/TTL 캐시(1h·meta 6h) + Athena 동시 세마포어(2) + 타임아웃 시 서버측 쿼리 취소(504). vin/signal_key는 정규식 화이트리스트(자유 SQL 없음).

| Method | Path | 설명 | 특이사항 |
|---|---|---|---|
| GET | `/api/v1/admin/datalake/meta?include_sim=0/1&no_cache=` | Silver VIN 목록·기간·이벤트 수(+RDS display_name/model 조인·없으면 null) | 30일 룰 유일 예외(컬럼 프루닝+6h 캐시)·SIM 기본 제외 |
| GET | `/api/v1/admin/datalake/signals?vin=&from_ts=&to_ts=` | 윈도우 내 signal_key 목록+빈도(신호 선택용) | 윈도우 ≤30일 |
| GET | `/api/v1/admin/datalake/series?vin=&signals=a,b&from_ts=&to_ts=&points=` | 신호(≤5) 시계열 — 시간버킷 avg 다운샘플(신호당 ≤points·ceil 버킷) | 숫자(num_value)만·`truncated` cap-hit 플래그 |
| GET | `/api/v1/admin/datalake/validation?from_ts=&to_ts=&limit=` | Bronze 검증 상세 — 상태/실패코드 분포+실패 샘플(사유·필드) | 윈도우=ingested_at·NULL ingested_at 항상 포함 |
| GET | `/api/v1/admin/datalake/battery-cells?vin=&from_ts=&to_ts=&points=` | 셀(brick) 전압 min/max·스프레드 시계열 | RDS에 없는 셀 레벨 심화·`truncated` 플래그 |

#### 중복 데이터 점검·정리 (`/api/v1/admin/duplicates`) — v1.6.9
| Method | Path | 요약 | 가드 |
|---|---|---|---|
| GET | `/api/v1/admin/duplicates/overview` | 중복 점검 상태(idle/scanning/cleaning) + 마지막 검사·정리 결과 (즉시 응답·무거운 쿼리 없음) | — |
| POST | `/api/v1/admin/duplicates/scan` | 🟢 telemetry_events 중복 검사 시작(**백그라운드**) — (vehicle_id,timestamp) 중복을 exact(payload 동일)/collision(payload 상이)으로 분류 | 409(작업 중) |
| POST | `/api/v1/admin/duplicates/cleanup?confirm=DELETE_DUPLICATES` | 🔴 완전중복(exact)만 제거(**백그라운드**) — 그룹당 keeper(typed non-null 최다, 동률 시 id 최소) 1행 보존·event_count 실측(RETURNING) 차감·**timestamp 윈도우(10만 행) 청크**로 소진까지(디스크 스필 차단) | 412(confirm)·409(작업 중) |

#### 장애 이메일 알림 (`/api/v1/admin/alerts`) — v1.7.2
| Method | Path | 요약 | 가드 |
|---|---|---|---|
| GET | `/api/v1/admin/alerts/status` | 알림 ON/OFF(`enabled`)·RDS 저장공간 알람 상태(`alarm_state`: OK/ALARM/INSUFFICIENT_DATA/MISSING)·토픽 존재(`topic_configured`)·수신 이메일 구독 목록(`subscriptions[].{email,protocol,confirmed,subscription_arn}` — `confirmed`=수신함 확인 링크 클릭 완료 여부, **확인된 구독만 실제 메일 수신**)·**RDS 용량 현황**(`rds_storage`: `{free_gib,allocated_gib,used_gib,used_pct,max_gib,threshold_gib,measured_at}` — CloudWatch FreeStorageSpace+RDS 할당/오토스케일 천장, IAM 미적용·조회 실패 시 **null**(graceful)) | 502(AWS 조회 실패) |
| POST | `/api/v1/admin/alerts/toggle?enabled=` | 알림 ON/OFF 토글 — CloudWatch 알람 `actions_enabled` enable/disable(ON이어야 이메일 발송). **기본 OFF**(terraform) | 502 |
| POST | `/api/v1/admin/alerts/email` | 수신 이메일 추가 — SNS `subscribe`(확인 메일 발송, 수신함에서 1회 confirm 필요). body `{email}` | 422(형식)·502 |
| DELETE | `/api/v1/admin/alerts/email` | 확인된 수신 이메일 삭제 — SNS `unsubscribe`. body `{subscription_arn}`(ops-alerts 토픽 구독만 허용) | 400(미확인/타 토픽)·502 |

> 알림 대상: 현재 **RDS FreeStorageSpace < 2GiB**(DiskFull 사고 재발 방지) 하나. SNS 토픽 `teslafleet-dev-ops-alerts` + 알람 `teslafleet-dev-rds-free-storage`는 terraform(`infra/envs/dev/alerts.tf`)이 생성하되 **구독(수신 메일)은 terraform이 만들지 않고 Admin UI가 boto3로 전담**(terraform/UI 충돌 회피). 알람 기본 OFF·`lifecycle ignore_changes=[actions_enabled]`로 런타임 토글 보존. consumer stall/24h 무적재 알람은 컨테이너 로그가 CloudWatch에 없어(json-file) 백엔드 커스텀 메트릭 publisher 필요 → 추후 확장.

> ⚠️ **전달 규칙**: 메일은 ① 알림 ON(`toggle?enabled=true`) ② 알람 발화(<2GiB) ③ **확인된(confirmed) 구독자 ≥1명** 세 조건이 모두 충족돼야 발송된다. SNS는 **확인된 구독에만** 전달하므로 미확인(PendingConfirmation) 이메일은 못 받고, **ON인데 confirmed 0이면 silent 무전달**(UI가 경고). 수신 구독은 **로그인 계정(accounts)과 별개** — `ADMIN_EMAIL`이어도 자동 구독되지 않으며 목록에 추가·확인해야 수신.

> 인증: admin 영역(`settings`/`admin/sim`/`admin/seed`/`admin/bronze-replay`/`admin/kafka-lag`/`admin/lakehouse`/`admin/duplicates`/`admin/accounts`/`admin/alerts`)은 **admin 세션 또는 `X-Admin-Key` 헤더 필요**(`ADMIN_AUTH_ENFORCE=1` 시 불일치/누락 401, `ADMIN_API_KEY`와 상수시간 hmac 비교). 2026-06-10: `/api/v1/customers` 변이 5개도 `require_admin_account` 부착(GET 2개는 `require_account`). ⚠️v1.7.0부터 `/geocode`·`/roads`도 `require_account`(무인증 아님) — 무인증은 `onboard.*`/`auth.*` 뿐. `admin/accounts` 파괴작업은 admin 세션 전용(X-Admin-Key 차단). 상세 [2.1 인증](#21-인증).

#### 고객사 (`/api/v1/customers`) — Alembic 0030
| Method | Path | 요약 | 가드 |
|---|---|---|---|
| GET | `/api/v1/customers` | 전체 고객사 + `vehicle_count` + `account_emails`(분배된 계정 이메일 — **admin/scope=None 응답에만** 채움, manager는 `[]`) | `require_account` |
| POST | `/api/v1/customers` | 생성(`{name}`, UNIQUE → 409) | `require_admin_account` |
| GET | `/api/v1/customers/{id}` | 단건 + `vehicles[]` inline + `account_emails`(admin만) + **`accounts:[{id,email}]`**(AccountBrief — 인라인 분배 해제용·admin scope=None만, v1.7.6) | `require_account` |
| PATCH | `/api/v1/customers/{id}` | 고객사 이름 수정(`{name}`, UNIQUE → 409) | `require_admin_account` |
| DELETE | `/api/v1/customers/{id}` | vehicles 0건일 때만 허용(409 가드) | `require_admin_account` |
| POST | `/api/v1/customers/{id}/vehicles` | 차량 일괄 추가(`{vehicle_ids[]}`) | `require_admin_account` |
| DELETE | `/api/v1/customers/{id}/vehicles` | 차량 일괄 제거 (같은 customer만) | `require_admin_account` |

#### 차량 carry-forward (`/api/v1/vehicles/{id}`)
| Method | Path | 요약 | 가드 |
|---|---|---|---|
| GET | `/api/v1/vehicles/{id}/latest` | latest_telemetry JSONB snapshot | — |
| POST | `/api/v1/vehicles/{id}/refill-latest-snapshot` | admin carry-forward backfill (차량별) | — |
| POST | `/api/v1/vehicles/admin/backfill-identity` | **차량 identity 1회 보강(v1.7.3)** — model(VIN 4번째 자리 디코드)·display_name(telemetry_events.raw_data 최신 `VehicleName`). 배포 consumer와 동일 정책(model='Unknown'·display_name placeholder만, 수동·실명 보존). 멱등. UPDATE는 str(id) 정렬·`lock_timeout=3s`(라이브 consumer 경합 시 fast-fail skip)·name 조회는 placeholder 차량만(`statement_timeout=30s`·SAVEPOINT 격리). 응답 `{updated,total,changes[],name_unresolved,name_timed_out,name_failed,lock_skipped}`(뒤 4개 0이 정상) | **admin**(require_admin_account) |

> `GET /api/v1/vehicles`에 `?customer_id=<uuid>` 필터 + 응답 `latest_telemetry`/`customer_id` inline (메인 현황 N+1 제거). v1.5.x: lat/lng가 latest_telemetry에 없으면 `telemetry_events` DISTINCT ON으로 1 SQL fallback 자동 채움.

#### Tesla 파트너 (CR-3) · 좌표→주소 · 도로 스냅 (옵션)
| Method | Path | 요약 | 가드 |
|---|---|---|---|
| GET | `/.well-known/appspecific/com.tesla.3p.public-key.pem` | partner_accounts 등록용 public key serve. env `TESLA_PARTNER_PUBLIC_KEY_B64` 미설정이면 404. | — |
| GET | `/api/v1/geocode/reverse?lat=&lng=&lang=ko\|en` | 좌표→주소(reverse geocoding) — server-side Google Geocoding API + reverse_geocodes 캐시(Alembic 0032). **현재 frontend는 client-side 직접 호출(NEXT_PUBLIC 키 + sessionStorage 캐시) — 이 endpoint는 옵션**. (v1.8.1) **per-account rate cap 120건/분** — 캐시 miss(=실제 Google 호출)에만 카운트(캐시 hit 비throttle), 초과 시 `status="rate_limited"`·`address_full=null`(DB 미기록→재시도 가능) | — |
| POST | `/api/v1/roads/snap` | 경로 점들을 **Google Roads API(snapToRoads)**로 실제 도로에 스냅 — **유료**. body `{"points":[{"lat","lng","ts"}]}` → `{"points","requests","status","error"}`. Roads API는 브라우저 CORS 미지원이라 **반드시 server-side 프록시**(키 client 미노출). 요청당 100점·입력 최대 2500점(균등 thinning). 2026-06-10: 실제 요청 **하드 예산 50**(경계 overlap+interpolate=false fallback 반영 — 도달 시 부분 결과 대신 passthrough `status=error`) + 좌표 범위 검증(lat ±90/lng ±180, NaN/inf 거부 → 422). 키 미설정 시 status=disabled. (v1.8.1) **per-account rate cap 30건/분** — 초과 시 `status="rate_limited"`·`points`=원경로 passthrough(호출 1건당 최대 50 Google 요청이라 폭주 방지). 차량 상세 경로의 '도로 보정' 토글에서만 호출. **⚠️ 한국 미지원**: 지도데이터 국외반출 규제로 Google Roads/Directions가 한국에서 동작 안 함(실측: HTTP 200·snappedPoints 0) → 프런트가 `isRoadSnapSupported`(한국 bbox)로 토글을 **숨김**. 지원 지역(한국 밖) 경로에서만 노출·호출됨. (2026-02 한국 조건부 반출 허용 → 연내 정식 지원 예정.) | — |

### 3.0.1 curl 복붙 모음

`export BASE=https://sphere.tesla.modapl.dev` 후 원하는 줄을 복붙. 🟢 안전(read) · 🔴 destructive(실행 전 확인). 사용법 상세 [2.6](#26-curl-빠른-테스트-사용법).

```bash
export BASE=https://sphere.tesla.modapl.dev

# ── 헬스체크 (🟢) ──
curl -sS $BASE/health
curl -sS $BASE/health/db

# ── 인증 (🟢 GET / 🔴 refresh) ──
curl -sS -i "$BASE/api/v1/auth/login"            # 302 Location 확인 (-i)
# callback은 Tesla redirect 전용 — 직접 호출 불가 (code/state 필요)
curl -sS -X POST "$BASE/api/v1/auth/refresh/<owner_id>" -H "X-Admin-Key: $ADMIN_KEY"   # 🔴 토큰 재발급 (v1.7.0 admin 가드)

# ── 온보딩 (인증: OAuth callback이 발급한 tf_onboard_owner 세션 쿠키. owner_id 쿼리는 무시(IDOR 방지), 쿠키 없음/변조/만료(30일) 시 401 reauth_required) ──
curl -sS -b 'tf_onboard_owner=<owner_id>.<issued_epoch>.<hmac>' "$BASE/api/v1/onboard/products"   # 🟢
curl -sS -b 'tf_onboard_owner=<owner_id>.<issued_epoch>.<hmac>' "$BASE/api/v1/onboard/vehicles"   # 🟢
curl -sS -b 'tf_onboard_owner=<owner_id>.<issued_epoch>.<hmac>' -X POST "$BASE/api/v1/onboard/register/<vin>"  # 🔴 Tesla config push

# ── 차량 (🟢) ──
curl -sS "$BASE/api/v1/vehicles"
curl -sS "$BASE/api/v1/vehicles?data_source=live"          # 🟢
curl -sS "$BASE/api/v1/vehicles?data_source=seeded"        # 🟢 Alembic 0024 비정규화로 504 해소
curl -sS "$BASE/api/v1/vehicles/stats"
VID=$(curl -sS "$BASE/api/v1/vehicles" | python3 -c 'import sys,json;print(json.load(sys.stdin)[0]["id"])')  # 첫 차량 id
curl -sS "$BASE/api/v1/vehicles/$VID"

# ── 텔레메트리 (🟢) — $VID 위에서 확보 ──
curl -sS "$BASE/api/v1/telemetry/vehicles/$VID/events?limit=1000&last_days=1"
curl -sS "$BASE/api/v1/telemetry/vehicles/$VID/alerts?limit=2000&last_days=1"
curl -sS "$BASE/api/v1/telemetry/vehicles/$VID/latest"

# ── 설정 ──
curl -sS "$BASE/api/v1/settings/known-signals"          # 🟢
curl -sS "$BASE/api/v1/settings/telemetry-config"       # 🟢
curl -sS -X PUT "$BASE/api/v1/settings/telemetry-config?confirm=APPLY_CONFIG" \
  -H 'Content-Type: application/json' \
  -d '{"signals":[{"signal_name":"VehicleSpeed","interval_seconds":5,"enabled":true,"display_order":1}],"cost_per_record_usd":0.0001,"assumed_active_hours_per_day":5,"assumed_vehicle_count":10}'   # 🔴 replace-set
curl -sS -X POST "$BASE/api/v1/settings/repush-all?confirm=REPUSH_ALL"   # 🔴 전체 차량 재push, 5분 cooldown

# ── 시뮬레이터 ──
curl -sS "$BASE/api/v1/admin/sim/runs"                  # 🟢
curl -sS "$BASE/api/v1/admin/sim/data-summary"          # 🟢
curl -sS "$BASE/api/v1/admin/sim/delete-events"         # 🟢
curl -sS -X POST "$BASE/api/v1/admin/sim/start" \
  -H 'Content-Type: application/json' \
  -d '{"vins":["SIM-TEST01"],"interval_seconds_override":30,"scenario":"driving"}'   # 🔴 sim run 시작
RID=<run_id>; curl -sS "$BASE/api/v1/admin/sim/runs/$RID"
curl -sS -X POST "$BASE/api/v1/admin/sim/stop/$RID"     # 🔴 sim run 중지
curl -sS -X DELETE "$BASE/api/v1/admin/sim/vehicles?confirm=DELETE_ALL_SIM"   # 🔴 SIM 전체 삭제, 5분 cooldown

# ── Seed 관리 ──
curl -sS "$BASE/api/v1/admin/seed/monthly-overview"     # 🟢 S3↔DB 비교 (600s 캐시)
curl -sS "$BASE/api/v1/admin/seed/imports?limit=50"     # 🟢 적재 audit
curl -sS "$BASE/api/v1/admin/seed/list-month-files?year=2025&month=11"   # 🟢
curl -sS "$BASE/api/v1/admin/seed/delete-jobs/<job_id>" # 🟢 삭제 job 진행
curl -sS -X POST "$BASE/api/v1/admin/seed/ingest-one?s3_key=<key>&confirm=SCAN_S3"   # 🔴 단일 파일 적재
curl -sS -X DELETE "$BASE/api/v1/admin/seed/events?year=2025&month=11&confirm=DELETE_SEEDED_MONTH"   # 🔴 월별 삭제 → 202+job_id
curl -sS -X DELETE "$BASE/api/v1/admin/seed/vehicles/<seeded_vehicle_id>?confirm=DELETE_SEEDED"      # 🔴 차량별 삭제 → 202+job_id
```

> 🔴 destructive는 실제 데이터를 변경/삭제합니다. seeded 차량/SIM 대상으로만 테스트하고, `repush-all`·`register`는 실 Tesla API를 호출하므로 운영 영향을 인지하고 실행하세요.

---

### 3.1 헬스체크 (`/health`)

#### `GET /health`
프로세스 살아있는지 확인. DB 의존 없음.

**Response 200**
```json
{ "status": "ok" }
```

#### `GET /health/db`
DB 연결 확인 (`SELECT 1` 실행). DB 다운 시 500.

**Response 200**
```json
{ "status": "ok" }
```

---

### 3.2 인증 (`/api/v1/auth`)

Tesla OAuth 2.0 인가 코드(authorization code) 흐름. 차주가 자기 Tesla 계정 데이터 접근을 우리 서비스에 허용하는 절차.

#### `GET /api/v1/auth/login`
Tesla OAuth authorize 페이지로 302 redirect. CSRF 방지용 state를 `tesla_oauth_state` 쿠키에 저장(10분).

**Query parameters** — 없음

**Response 302**
- `Location`: `https://auth.tesla.com/oauth2/v3/authorize?response_type=code&client_id=...&redirect_uri=...&scope=...&state=...&prompt_missing_scopes=true`
- `Set-Cookie`: `tesla_oauth_state=<random>; Domain=.tesla.modapl.dev; Max-Age=600; HttpOnly; Secure; SameSite=Lax` — 2026-06-10: cross-subdomain domain 추가(onboard host에서 시작한 로그인이 sphere callback에서 state 검증 실패하던 것 fix)

**스코프** (config.py `tesla_oauth_scopes`)
- `openid` · `offline_access` · `vehicle_device_data` · `vehicle_location` · `vehicle_cmds`
- `vehicle_charging_cmds`는 2026-06 audit에서 제거(데이터 수집 전용 — 충전 제어 명령 경로 없어 최소권한 위반). `vehicle_location`은 GPS/속도/Shift state 신호에 필수.

**Errors**
- `500` — `tesla_client_id` 미설정.

#### `GET /api/v1/auth/callback`
Tesla 인가 코드 → access/refresh token 교환 후 DB 저장. 성공 시 onboard로 redirect.

**Query parameters (required)**
| name | type | 설명 |
|---|---|---|
| `code` | string | Tesla가 redirect URL에 붙여준 인가 코드 |
| `state` | string | login에서 발급한 state — 쿠키 값과 일치해야 함 |

**Cookie**
- `tesla_oauth_state` (required) — `state` query와 일치해야 함

**Response 302**
- `Location`: `https://onboard.tesla.modapl.dev/onboard/vehicles?owner_id=<id_token.sub>` — 차주 선택 페이지(2026-06-10 fix: 이전 `/vehicles`는 관리자 페이지였음)
- `Set-Cookie`: `tf_onboard_owner=<owner_id>.<issued_epoch>.<hmac>; Domain=.tesla.modapl.dev; Max-Age=2592000; HttpOnly; Secure; SameSite=Lax` — onboard endpoint 인증용 HMAC 서명 세션(`sign_owner(owner_id)`, 30일). 2026-06-10: 서명에 발급시각 포함 — 서버측 30일 만료 강제(탈취 쿠키 영구 유효 차단), 구 2-세그먼트 포맷은 거부(재로그인 1회). cross-subdomain(sphere callback → onboard.* endpoint) 공유. onboard.* 인증의 유일한 출처(URL의 owner_id는 표시용·불신).

**저장 동작** (DB `vehicle_owner_tokens` 테이블)
- `owner_id` = id_token `sub` (없으면 `ouid`)
- `owner_email` = id_token `email`
- access/refresh token = KMS envelope 암호화 6컬럼 (`access_token_ct/nonce/dek`, `refresh_token_ct/nonce/dek`)
- `token_expires_at` = 현재 시각 + `expires_in`초 (기본 3600)
- `scopes` = config의 OAuth scopes 배열

**Errors**
- `400` — `"Invalid OAuth state (CSRF protection)"` (state 누락/불일치) · `"Tesla token exchange failed: ..."` (Tesla 응답 body 마스킹 후 detail에 포함)
- `500` — 5가지 케이스:
  - `"Tesla credentials not configured"` (client_id/secret 미설정)
  - `"Token response missing access/refresh token"` (Tesla 응답에 access_token/refresh_token 누락)
  - `"Tesla OAuth response missing id_token"` (id_token 누락 — scope `openid` 확인 필요)
  - `"Tesla id_token missing sub/ouid claim"` (id_token payload에 `sub`/`ouid` 둘 다 없음)
  - `"Tesla id_token decode failed: ..."` (base64/JSON 디코드 실패)

#### `POST /api/v1/auth/refresh/{owner_id}`
저장된 refresh_token으로 access_token 재발급. PostgreSQL에서는 `SELECT ... FOR UPDATE`로 동시 refresh를 직렬화.

> **v1.7.0**: `require_admin_account` 가드(admin 세션 또는 X-Admin-Key) — Basic auth 제거로 공개되던
> 것을 차단(비인증 호출자가 Tesla single-use refresh 회전을 임의 트리거하는 abuse 방지). 운영용.

**Path parameters**
| name | type | 설명 |
|---|---|---|
| `owner_id` | string | id_token sub 값 (callback 저장 시 키) |

**Response 200**
```json
{
  "status": "refreshed",
  "owner_id": "1293ebe9-...",
  "expires_at": "2026-05-14T11:30:00+00:00"
}
```

**Errors**
- `400` — `"Refresh failed: ..."` (Tesla refresh API non-200, 응답 body 마스킹)
- `404` — `"No token found for owner_id={owner_id}"`
- `502` — `"Tesla refresh response missing access_token"` (Tesla 200인데 access_token 누락 — auth.py·onboard._get_access_token 공통 방어)

---

### 3.3 온보딩 (`/api/v1/onboard`)

차주가 본인 Tesla 차량을 우리 telemetry server에 등록하는 흐름.

#### `GET /api/v1/onboard/products`
owner의 Tesla 차량(+에너지 제품) 목록. Tesla `GET /api/1/products` proxy.

**인증** — `owner_id`는 `Depends(get_authenticated_owner)`로 HMAC 서명 세션 쿠키(`tf_onboard_owner`)에서만 얻는다. **쿼리 파라미터 `owner_id`는 무시**(IDOR 방지, 2026-06 audit). 쿠키 없음/변조 시 `401 reauth_required`.

**Query parameters** — 없음 (인증된 owner_id는 쿠키에서 도출)

**Response 200** — Tesla API 응답 그대로 (`json_utf8`로 한글 유지)
```json
{
  "response": [
    { "id": 123, "vehicle_id": 456, "vin": "5YJ...", "display_name": "Model 3", "state": "online" }
  ],
  "count": 1
}
```

**Errors**
- `4xx/5xx` — Tesla 응답 status를 그대로 전파 (`HTTPException(resp.status_code, ...)`)
- 토큰 만료 시 internal refresh 자동 시도 (`_get_access_token`). 실패 시 `401` (Refresh failed) · `404` (token row 없음)

#### `GET /api/v1/onboard/vehicles`
`/products` + Tesla `GET /api/1/vehicles/fleet_status`를 합쳐 페어링 상태 enrich. frontend가 1회 호출로 전체 정보 획득.

**인증** — `Depends(get_authenticated_owner)`로 세션 쿠키(`tf_onboard_owner`)에서 owner_id 도출. 쿼리 owner_id 불신(IDOR 방지). 쿠키 없음/변조 시 `401 reauth_required`.

**Query parameters** — 없음 (인증된 owner_id는 쿠키에서 도출)

**Response 200**
```json
{
  "vehicles": [
    {
      "vin": "5YJ...",
      "display_name": "Model 3",
      "vehicle_id": 456,
      "state": "online",
      "paired": true,
      "firmware_version": "2026.4.2",
      "vehicle_command_protocol_required": true,
      "fleet_telemetry_version": "0.3.2"
    }
  ],
  "pairing_url": "https://tesla.com/_ak/sphere.tesla.modapl.dev",
  "fleet_status_available": true
}
```

- `paired`: `true` / `false` / `null`(Tesla가 응답에 포함 안 함 — unknown)
- `fleet_status_available`: fleet_status 호출 성공 여부. `false`면 vehicles 배열의 `paired` 등 enrich 필드는 모두 `null`

**Errors** — `/products`와 동일 (fleet_status 실패는 silent fallback)

#### `POST /api/v1/onboard/register/{vin}`
차량에 `fleet_telemetry_config` push. 우리 telemetry server hostname/port + CA cert + 신호 fields를 차량에 등록. 실 호출 경로 = `POST {fleet_api_base}/api/1/vehicles/fleet_telemetry_config`(onboard.py).

> ⚠️ **보류(첫 실차주 온보딩 전 필요)**: Tesla 공식상 `fleet_telemetry_config` create는 **vehicle-command 프록시 서명** 경유가 권장된다. 본 앱은 `.well-known` 공개키 등록 방식이라 미서명 직접 push는 현행 펌웨어(2024.26+) 실차량에서 **skipped/거부**될 수 있다. 차주 0건이라 현재 미발현 — 첫 실차주 전 `tesla-http-proxy` 사이드카 도입 필요(memory `tesla_config_signing_pending`).

**인증** — `Depends(get_authenticated_owner)`로 세션 쿠키(`tf_onboard_owner`)에서 owner_id 도출. 쿼리 owner_id 불신(IDOR 방지 — 차주 A가 `?owner_id=B`로 B 자원 등록 차단). 쿠키 없음/변조 시 `401 reauth_required`.

**Path parameters**
| name | type | 설명 |
|---|---|---|
| `vin` | string | 등록할 차량의 VIN |

**Query parameters** — 없음 (인증된 owner_id는 쿠키에서 도출)

**Request body** — 없음 (서버가 DB에서 fields 로드)

**Response 200**
정상 push:
```json
{
  "status": "ok",
  "vin": "5YJ...",
  "synced": null,
  "message": "Fleet telemetry config 전송 완료. 차량이 온라인이면 즉시, 아니면 다음 backend 연결 시 적용됩니다.",
  "tesla_response": { /* Tesla 응답 raw */ }
}
```
- `synced`: 2026-06-10 Tesla 공식 대조 — synced/limit_reached는 `GET /{vin}/fleet_telemetry_config` 응답 전용 필드라 **create 응답엔 없어 항상 `null`**(즉시/wake 분기 메시지 제거, 단일 안내로 정리). 실제 동기화 확인은 GET 조회 필요(`onboard.py:_extract_config_status`).

페어링 필요 (Tesla 412):
```json
{
  "status": "needs_pairing",
  "vin": "5YJ...",
  "pairing_url": "https://tesla.com/_ak/sphere.tesla.modapl.dev",
  "message": "이 차량에 우리 앱의 public key가 페어링되지 않았습니다. ...",
  "tesla_status": 412,
  "tesla_response": "..."
}
```
*HTTP status는 200* — 차주 안내용 actionable 상태. `tesla_response`는 `safe_response_text(resp.text, limit=300)`로 마스킹 + 300자 절단된 raw 텍스트.

**비정상 응답 본문 shape 차이**
- `status="needs_pairing"` 분기 — `tesla_response`: **300자 절단된 raw 텍스트** (`safe_response_text(text, limit=300)`, token reflection 방지 마스킹 포함). 별도 `tesla_status` 필드도 포함.
- `status="error"` 분기 — `tesla_response` **필드 없음**. `message`가 `"Tesla API {status_code}: {raw_text[:300]}"` 형태로 응답 텍스트를 임베드. (2026-05-14) `invalid_signals: string[]` 필드 추가 — Tesla 응답에서 `parse_invalid_signals`로 추출한 거부 신호명 list. 빈 list면 일반 오류.
- `status="ok"` / `status="limit_reached"` 분기 — `tesla_response`: **Tesla 응답을 JSON parse한 dict 전체** (절단 없음). JSON parse 실패 시에만 300자 raw 텍스트 fallback.

**Errors**
- `400` — Tesla 응답이 200/201/412 외 (`status:"error"` 본문 + `message` 포함)
- `401` — `_get_access_token` 내부 refresh 실패 (`"Refresh failed: ..."`)
- `404` — `_get_access_token`에서 `owner_id`에 대한 토큰 row 없음 (`"No token for owner_id={owner_id}"`)
- `502` — Tesla refresh 응답에 access_token 누락 (`_get_access_token` 내부, `"Tesla refresh response missing access_token"`)
- `409` — Tesla 응답에 `limit_reached=true`(skipped_vehicles.max_configs) — 한 차량 동시 **최대 5개** third-party 슬롯 도달. `status:"limit_reached"`. (firmware/hardware 미지원 skip도 409 `status:"error"`.)
- `500` — `TESLA_TELEMETRY_CA_CERT_B64` 미설정 · base64/UTF-8 디코드 실패 · 활성화된 신호 0개 (`_load_signal_fields`)

---

### 3.4 차량 (`/api/v1/vehicles`)

DB에 적재된 차량 메타 + telemetry 통계 조회. Tesla API와 무관 — 로컬 DB만 사용.

#### `GET /api/v1/vehicles`
차량 목록 + 차량별 적재된 telemetry events 통계.

**Query parameters**
| name | type | default | 설명 |
|---|---|---|---|
| `include_simulated` | bool | `false` | `true`면 `SIM-` 차량 포함 |
| `data_source` | enum\|null | `null` | `live`/`seeded`/`simulated` 필터. 미지정 시 `include_simulated`만 적용. invalid 값은 422 |
| `customer_id` | UUID\|null | `null` | 고객사 필터 (Alembic 0030). 미지정 시 전체 |

**Errors**
- `400` — `data_source=simulated` 인데 `include_simulated=false` (모순 조합. `include_simulated=true`와 함께 호출 필요)
- `422` — `data_source`가 enum(`live`/`seeded`/`simulated`) 외 값

**Response 200** — `list[VehicleListItem]` (display_name ASC)
```json
[
  {
    "id": "5e7f...",
    "vin": "5YJ...",
    "display_name": "Model 3",
    "model": "Model 3",
    "color": "Pearl White",
    "software_version": "2026.4.2",
    "is_simulated": false,
    "data_source": "live",
    "customer_id": null,
    "created_at": "2026-05-11T01:00:00+00:00",
    "updated_at": "2026-05-14T01:00:00+00:00",
    "event_count": 12345,
    "earliest_timestamp": "2026-05-11T01:00:00+00:00",
    "latest_timestamp": "2026-05-14T00:59:00+00:00",
    "latest_telemetry": { "latitude": 37.5, "longitude": 127.0, "battery_level": 82 }
  }
]
```

#### `GET /api/v1/vehicles/stats`
실 차량 vs SIM 차량 카운트.

**Response 200**
```json
{
  "real_count": 5,
  "simulated_count": 2,
  "total_count": 7,
  "by_source": { "live": 5, "seeded": 0, "simulated": 2 }
}
```

`by_source`는 data_source 3분류(`live`/`seeded`/`simulated`) 카운트 — 항상 반환.

#### `GET /api/v1/vehicles/{vehicle_id}`
단일 차량 메타 (events 통계 없음).

**Path parameters**
| name | type | 설명 |
|---|---|---|
| `vehicle_id` | UUID | 차량 PK |

**Response 200** — `VehicleSummary`
```json
{
  "id": "5e7f...",
  "vin": "5YJ...",
  "display_name": "Model 3",
  "model": "Model 3",
  "color": "Pearl White",
  "software_version": "2026.4.2",
  "is_simulated": false,
  "data_source": "live",
  "customer_id": null,
  "created_at": "2026-05-11T01:00:00+00:00",
  "updated_at": "2026-05-14T01:00:00+00:00"
}
```

**Errors**
- `404` — `{"detail":"Vehicle not found"}`

---

### 3.5 텔레메트리 (`/api/v1/telemetry`)

DB에 적재된 telemetry events / alerts 조회. 시계열 sampling + carry-forward semantics 포함.

#### `GET /api/v1/telemetry/vehicles/{vehicle_id}/events`
시간 범위의 telemetry events. 결과 row 수가 `limit`을 넘으면 다운샘플 (2026-05-15 v1.0.3: row-sampling → **column-aware time-bucket**).

**Path parameters**
| name | type | 설명 |
|---|---|---|
| `vehicle_id` | UUID | 차량 PK |

**Query parameters**
| name | type | default | 제약 | 설명 |
|---|---|---|---|---|
| `from` | datetime (ISO 8601) | null | — | 범위 시작 (inclusive). 코드 alias: `from_ts` |
| `to` | datetime (ISO 8601) | null | — | 범위 종료 (inclusive). alias: `to_ts` |
| `last_days` | int | null | `≥ 1` | `from` 미지정 시 `max(timestamp) − last_days`를 from으로 자동 설정 |
| `limit` | int | `500` | `1~5000` | 반환 row 수 cap |

**Response 200** — `list[TelemetryEventOut]` (timestamp DESC). 응답 schema 상세: [4. 데이터 모델](#4-데이터-모델).

**Sampling 동작** (v1.0.3, 2026-05-15 갱신)
- total ≤ `limit` → 그대로 DESC 정렬 반환 (단, 아래 cap-hit 폴백 참조)
- **cap-hit 폴백(v1.7.6, PostgreSQL 한정)**: total(플래너 추정)이 `limit` 이하라 비다운샘플 분기로 진입했어도, 실제 fetch 결과가 **LIMIT cap에 도달**(`len == limit`)하면(=추정 과소) full-row 반환 대신 **다운샘플(time-bucket) 경로로 폴백**한다. 플래너 EXPLAIN 추정이 `vehicle_id × timestamp` 교차상관을 무시해 과소추정(실측 est≈100인데 실제 1.5만)할 때 '최신 limit건만' 반환→**요청 범위 침묵 절단** + raw_data 비결정성을 차단(2026-06-25 audit). cap 미달(`len < limit`)이면 진짜 소량이라 raw_data 포함 full-row 그대로. SQLite는 exact count라 폴백 제외.
- total > `limit` + **PostgreSQL** → **column-aware time-bucket aggregation**:
  시간을 `limit`개 bucket으로 `width_bucket`으로 균등 분할 후, 각 bucket에서
  **컬럼별 마지막 non-null 값** 추출 (`array_agg(col ORDER BY timestamp DESC) FILTER (WHERE col IS NOT NULL)[1]`).
  Tesla partial-update로 신호별 측정 빈도가 달라도 모든 신호가 bucket마다 대표됨
  (예: `energy_remaining_kwh` row-sampling 13점 → time-bucket 295점, 22×).
  점은 실제 측정값 (보간 아님). `timestamp` ASC 정렬.
- total > `limit` + **SQLite (테스트)** → 기존 row-sampling fallback
  (`ROW_NUMBER() % step`) — width_bucket/array_agg 미지원이라 dialect 분기
- **`raw_data`**: time-bucket path에서는 `null` 반환 (jsonb array_agg 성능 +
  frontend가 events raw_data를 화면 표시 안 함). total ≤ limit / SQLite
  fallback path에서는 그대로 채워짐
- **TTL 캐시**: time-bucket 결과를 `(vehicle, from, to, last_days, limit)` 키로
  캐시 (LRU cap 12 — route 캐시는 32). **TTL은 차량 `data_source`별 차등(commit bdcf724)**:
  live=60s / seeded·simulated=600s(10분, 정적 데이터라 width_bucket 재실행 분당→시간당↓).
  같은 차량/범위 반복 조회 시 cold ~9s → warm ~0.3s (대시보드 차트는 실시간 모니터링 아님).
  **v1.6.5**: 행 수 판단을 exact `count(*)` → **플래너 추정**(`EXPLAIN`, heap 미접근·ms급)으로
  전환 — 대범위(수백만 행) 차량의 exact count가 visibility map 미설정 시 수십 초라 타임아웃을
  유발하던 문제 해소(`_estimate_row_count`, SQLite는 exact 폴백). 안전망 행 상한 `_ROW_CAP=150k`
  초과 시 최근 150k행 시점으로 from 자동 축소(index-only OFFSET)해 bucket 집계 타임아웃 차단.
  **축소된 응답은 캐시하지 않음**(cache_key=user input 기준이라 정합 위반 방지).

**Errors**
- `404` — `{"detail":"Vehicle not found"}`
- `504` — `{"detail":"조회 기간이 너무 커서 시간이 초과되었습니다. 더 좁은 기간을 선택해 주세요."}`
  (bucket 집계 `statement_timeout=45s` 초과 — RDS 부하 스파이크·콜드 캐시 시 **페이징 청크에서도 단발 발생
  가능**. FE는 청크 1회 재시도→실패 청크만 건너뜀으로 흡수, 2026-06-11 b2f9da1)

#### `GET /api/v1/telemetry/vehicles/{vehicle_id}/events/count`  *(v1.6.5 신규)*
범위 내 event 수(플래너 **추정**) + 해석된 조회 창(`from`/`to`) + `row_cap`. **FE 점진 페이징**이 시간
청크 수/폭을 정하는 데 사용(가벼움). Query: `from`/`to`/`last_days`(events와 동일 해석). `last_days`는
`max(timestamp)` 기준 절대화, 무경계('전체')는 데이터 `min/max`로 창 해석.

**Response 200** — `{ "count": int, "from": ISO8601|null, "to": ISO8601|null, "row_cap": int }`.
**Errors**: `404` Vehicle not found.

> **점진 페이징(v1.6.5 · 2026-06-11 b2f9da1 실패 내성 보강)**: FE(`loadEventsProgressive`)는 ① `count`로
> 밀도 확인(transient 실패 시 1회 재시도) → ② 저밀도(≤50k)면 단일 fetch, 고밀도면 조회 창을 **시간 청크로
> 분할**해 순차 fetch. **첫 청크는 항상 '최근 1일'**(전체 태그여도 최근 1일을 먼저 표시), 이후 과거를 밀도
> 기반 청크(MAX 60개)로 누적 — 진행바로 서서히 채운다. 반열린 시간 경계로 겹침 없음.
> **실패 내성(b2f9da1)**: 청크가 timeout(45s 504/클라 60s)하면 **1회 재시도 → 그래도 실패하면 해당 청크만
> 건너뜀**(차트에 그 구간만 공백, 연속 2청크 실패 시 조기 중단). 건너뛴 청크가 있으면 `PartialLoadError`
> → UI는 `error.partialLoad`('일시 지연·재시도') 안내 — `rangeTooLarge`('기간 축소')가 아님. 단일 fetch가
> timeout해도 해석된 창이 있으면 throw 대신 **청크 경로로 폴백**(플래너 추정 과소평가 대비).

#### `GET /api/v1/telemetry/vehicles/{vehicle_id}/alerts`
차량 alerts 조회.

**Query parameters**
| name | type | default | 제약 | 설명 |
|---|---|---|---|---|
| `from` | datetime (ISO 8601) | null | — | alias `from_ts` |
| `to` | datetime (ISO 8601) | null | — | alias `to_ts` |
| `last_days` | int | null | `≥ 1` | events와 동일 (차량별 max(started_at) 기준) |
| `active_only` | bool | `false` | — | `true`면 `ended_at IS NULL` (진행 중) 만 |
| `limit` | int | `2000` | `1~10000` | — |

**Response 200** — `list[VehicleAlertOut]` (started_at DESC)

```json
[
  {
    "id": "9c2a...",
    "vehicle_id": "5e7f...",
    "name": "VCFRONT_a155_falconWingCloseDetectionFailure",
    "started_at": "2026-05-13T14:22:01+00:00",
    "ended_at": null,
    "audiences": ["Customer", "Service"],
    "received_at": "2026-05-13T14:22:02+00:00",
    "raw_data": { /* Tesla alerts message JSON */ }
  }
]
```

**Errors**
- `404` — `{"detail":"Vehicle not found"}`

#### `GET /api/v1/telemetry/vehicles/{vehicle_id}/latest`
가장 최근 telemetry 1건. 단, 컬럼별로 `null`이면 더 과거 row에서 가장 최근 non-null 값으로 채움 (carry-forward).

- 최대 2000건 walk back (timestamp DESC, id DESC secondary order).
- `raw_data`는 oldest→newest 순서로 dict `update()` merge (newer key가 older 덮어쓰기).
- `id`/`vehicle_id`/`timestamp`/`raw_data`는 carry-forward 제외.

**Response 200** — `TelemetryEventOut` (단일 객체, list 아님)

**Errors**
- `404` — `{"detail":"Vehicle not found"}` 또는 `{"detail":"No telemetry events for this vehicle"}`

---

### 3.5.1 차량 심화 분석 (`/api/v1/telemetry`) — v1.7.7

차량 상세 화면의 '심화 분석' 섹션이 사용하는 집계 API 10종(`backend/app/routers/analytics.py`, prefix `/telemetry` → 마운트 `/api/v1`). 전부 typed 컬럼만 사용해 events 다운샘플(raw_data 제외) 영향을 받지 않는다.

**공통 사양** (10개 모두):
- **메서드/인증**: 전부 `GET` · `require_account`(세션 쿠키 또는 X-Admin-Key, **추가 admin 가드 없음**). manager는 `customer_scope`로 자기 고객사 차량만 — 타 고객사 차량은 `404`(`fleet-baseline` 제외, 아래 참조).
- **파라미터**: `from`(alias)·`to`(alias)·`last_days`(≥1). `from` 미지정 + `last_days`면 차량별 `max(timestamp)` 기준 N일 전을 `from`으로 계산(telemetry route 패턴).
- **캐시**: 결과 LRU 캐시(최대 64). TTL = **live 300s / 정적(seeded·simulated) 1800s**(`_analytics_ttl` — 추세라 staleness 무해). `fleet-baseline`은 600s 공유 캐시.
- **타임아웃**: PostgreSQL은 `SET LOCAL statement_timeout = 60s`(telemetry events/route의 45s보다 김 — cold-cache 첫 집계가 무거움). 초과 시 **`504 {"detail":"range_too_large"}`**(무경계/초장기간은 범위 축소 안내). 0047/0048/**0049/0050** 분석 가속 인덱스로 cold 첫 조회를 완주시키고 캐시에 적재(0049: charge-sessions 부분 인덱스 정밀 일치로 sticky 행 heap 스캔 504 제거 / 0050: places 커버링 부분 인덱스로 lat/lng index-only scan, seq scan 504 제거).
- **404**: `{"detail":"Vehicle not found"}`.

| Path | # | 설명 |
|---|---|---|
| `GET /vehicles/{vehicle_id}/charge-sessions` | #1,#8 | 충전 세션 분할(20분 간격 분리) + 세션별 SoC/에너지(Δenergy_remaining 우선·없으면 전력 적분)/평균·피크 전력/AC·DC 판정/위치 + SoC vs kW **충전 곡선**(≤80점). ⭐**충전 판정 = `charge_state='Charging'` AND 정지(`speed_kph≤1` 또는 NULL) AND `charging_power_kw>0`**. 1차 신호는 charge_state(전력은 단독 신뢰 불가 — 전력>1 샘플의 84~88%가 Disconnected/Idle), 정지·전력>0은 보조 가드: carry-forward가 충전 종료 전이 누락 시 'Charging'을 주행 내내(speed>1) 또는 종료 후 정차(전력=0) 고착(라이브 2026-06-29: Yuna 'Charging'의 80%가 speed>1)→세션 오염. 두 가드로 실충전만(라이브 정밀 99%+: 정지 6,758행 중 6,713이 전력 보유). 각 세션에 **`soc_unreliable`**(bool — SoC 진폭이 순변화보다 5%p 이상 크면 비단조 진동). cap(60000) 초과 시 `truncated=true`. **`habits`**(v1.7.9, 충전 습관/스트레스 점수 — 같은 세션 집계·추가 쿼리 0): `{score(0~100·null=세션<3), session_count, soc_session_count, dc_ratio, high_soc_ratio, deep_discharge_ratio, avg_start_soc, avg_end_soc}`. 점수=DC 급속 비율(0.40)·종료 SoC≥90% 비율(0.35)·시작 SoC≤10% 비율(0.25)의 서브점수 가중평균. **DC 서브점수는 `100−40·비율`(100% DC라도 60, 필요성 반영)**, SoC 2요인은 `100·(1−비율)`(전폭). SoC 지표는 `soc_unreliable=false` 신뢰 세션만이고 **신뢰 세션<3이면 SoC 요인 제외**(점수=DC만·`high_soc_ratio` 등 null)·전체 세션<3이면 `score=null`. FE는 SoC 제외 시 'SoC 표본 부족' 캐비엇 노출. |
| `GET /vehicles/{vehicle_id}/efficiency` | #2 | 일별 전비 — 일별 거리/에너지 = **daily-min-delta**(다음날 최소 odo/energy − 그날 최소). 윈도 max-min은 out-of-order replay+carry-forward로 미래값이 과거 날에 누출되면 부풀려져(라이브 실측 16배) daily-min-delta로 면역화. 마지막날만 within-day max-min(물리 1500km 캡). Wh/km [20,2000] 밖은 평균 제외. → km/kWh·Wh/km + 평균 외기온. KST 일 경계. `{points[], total_dist_km, total_energy_kwh, avg_km_per_kwh, avg_wh_per_km}` |
| `GET /vehicles/{vehicle_id}/driving-events` | #7 | 급가속/급감속/급선회 — `abs(longitudinal/lateral_acceleration)` 임계 초과 raw 샘플을 type+시간 간격으로 **클러스터링**(1 급조작=1 이벤트) + 100km당 빈도 → 운전 점수[0,100]. 점수 분모 dist_km는 **daily-min-delta**(누출 면역·efficiency와 동일·_window_dist_km). 파라미터 `accel_th`/`lat_th`(m/s², `ge=0.5 le=15.0`, 기본 3.0 — 기본이면 부분 인덱스 `ix_te_harsh_accel` 사용). `{events[≤500], counts, total_events, dist_km, events_per_100km, score, thresholds, speed_matrix, truncated}`. **`speed_matrix`**(v1.7.9)=전체 클러스터 이벤트를 속도밴드(0/30/60/90/120+ km/h)×유형(accel/brake/turn)으로 집계(`{bands[{lo,hi,accel,brake,turn}], unknown}`, 마지막 밴드 hi=null overflow·속도 미상은 unknown) — 표시캡 ≤500과 무관하게 정확. |
| `GET /vehicles/{vehicle_id}/speed-histogram` | #10 | 주행(속도≥1km/h) 속도 분포(0~200, 20버킷·10km/h 폭 + overflow) + avg/max/**p95(누적 버킷 근사)**. |
| `GET /vehicles/{vehicle_id}/places` | #9 | 자주 가는 장소 — 정차(속도≤3km/h) 샘플을 ~110m 격자로 묶어 방문 횟수·체류시간 랭킹(5분 미만 통과 방문 제외). centroid 좌표만 반환(주소는 FE reverse-geocode 캐시). 상위 8. |
| `GET /vehicles/{vehicle_id}/battery-health` | #11 | 배터리 건강도/열화 — RatedRange·EnergyRemaining를 SoC 정규화한 '100% 환산'(rated_range_km/(SoC/100)) 일별 추세 + (윈도 최대 대비) 열화%. SoC<30%는 정규화 노이즈로 제외. |
| `GET /vehicles/{vehicle_id}/vampire-drain` | #12 | 대기 방전 — 주차(속도≤1·비충전) 중 SoC 감소율(%/일). 시간당 버킷 선집계 후 연속 주차 구간 군집화. `{avg_pct_per_day, est_km_per_day, parked_hours, segment_count, segments[], truncated}` |
| `GET /vehicles/{vehicle_id}/activity-calendar` | #13 | 일별 운행 거리 — **daily-min-delta**(efficiency와 동일·누출 면역). 마지막날 within-day max-min(>1500km 글리치는 0). 음수 0 clamp. GitHub 기여도 캘린더 히트맵용. 전 일자 반환(0km 포함). KST 일 경계. `{days:[{day,dist_km}]}` |
| `GET /vehicles/{vehicle_id}/utilization` | #util | 가동률 + 커버리지 헬스. 연속 샘플 간격(dt)을 그 시점 상태로 귀속 — **속도 우선**(움직이면 주행, sticky 'Charging' 무력화)·**쿼리 시점 last-value 채움**(NULL은 직전 비-NULL 유지·적재 carry 여부 무관). 1시간 초과 dt는 '수집 공백'(차량 절전). PG는 window(`first_value` last-non-null + `LAG`) 단일 집계. `{driving_s, charging_s, parked_s, gap_s, *_pct, coverage_pct, utilization_pct(=주행/덮인시간), samples, samples_per_day, gap_count, longest_gap_s, gaps[]}` |
| `GET /fleet-baseline` | — | 시뮬 제외 **전 차량**의 전비·운전점수 가중 평균(비교 기준선). ⚠️ **`customer_scope` 미적용(의도적)** — 고객사 계정도 전체 플릿 평균을 기준으로 본다(단순 집계라 개별 차량 누설 위험 낮음, 수용). 한 차량 504면 그 차량만 제외하고 진행(견고·`driving.truncated`로 cap-hit 노출). |

---

### 3.6 설정 (`/api/v1/settings`)

Telemetry 수집 신호 + 비용 가정. admin UI(`/admin/settings/telemetry`)에서 호출.

#### `GET /api/v1/settings/known-signals` (2026-05-14 신규)
Tesla 공식 신호명 list + alias 매핑. frontend의 `<datalist>` 자동완성 + 미매칭 warning 용.

**Response 200**
```json
{
  "signals": ["AcChargingEnergyIn", "AcChargingPower", "BatteryHeaterOn", "..."],
  "aliases": { "ChargingState": "ChargeState" },
  "total": 256
}
```

- `signals`: Tesla `fleet-telemetry/protos/vehicle_data.proto`의 `Field` enum 전체 (정렬). 출처는 `backend/app/tesla_signals.py` — 갱신 시 `scripts/extract_tesla_signals.sh` 재실행 후 backend redeploy
- `aliases`: 잘못된 이름 → 정식 이름 매핑 (예: `ChargingState` → `ChargeState`). lesson 53 alias 매핑이 우회해 동작하지만 운영자가 즉시 발견하도록 별도 warning
- `total`: `len(signals)` (현재 256개)

**Errors**: 없음 (정적 데이터)
**캐시**: frontend `revalidate: 3600` (1시간)

#### `GET /api/v1/settings/telemetry-config`
현재 저장된 신호 설정 + 가정값 + 예상 비용.

**Response 200**
```json
{
  "signals": [
    {
      "signal_name": "VehicleSpeed",
      "interval_seconds": 5,
      "minimum_delta": null,
      "resend_interval_seconds": null,
      "enabled": true,
      "display_order": 1,
      "last_validation_status": "valid",
      "last_validation_at": "2026-05-14T18:02:00+00:00",
      "last_validation_error": null
    }
  ],
  "assumptions": {
    "cost_per_record_usd": 0.0001,
    "active_hours_per_day": 5.0,
    "vehicle_count": 10
  },
  "estimate": {
    "records_per_day_per_vehicle": 3600.0,
    "records_per_day_total": 36000.0,
    "records_per_month_total": 1080000.0,
    "cost_per_day_usd": 3.6,
    "cost_per_month_usd": 108.0,
    "cost_per_year_usd": 1314.0
  }
}
```

`assumptions` 기본값(app_settings row 없을 때) — DB에는 문자열 fallback으로 저장되지만 응답에서는 `float`/`int`로 캐스팅:
- `cost_per_record_usd`: DB fallback `"0.0001"` → 응답 `float` (예: `0.0001`)
- `active_hours_per_day`: DB fallback `"5"` → 응답 `float` (예: `5.0`)
- `vehicle_count`: DB fallback `"10"` → 응답 `int` (예: `10`)

`signals[].last_validation_*` (2026-05-14 추가, Alembic 0021):
- `last_validation_status`: `"valid" | "invalid" | "skipped" | null` — PUT 직후 비동기로 1대 차량에 Tesla push 시도 결과 반영
  - `valid`: Tesla 응답 200/201
  - `invalid`: Tesla 응답에서 `parse_invalid_signals`가 이 신호를 추출
  - `skipped`: 차량 0대 / Tesla 응답 파싱 실패 / 토큰 없음
  - `null`: 아직 한 번도 검증 안 됨
- `last_validation_at`: 검증 시각 (ISO-8601 with `+00:00`)
- `last_validation_error`: `invalid`/`skipped`일 때 Tesla 응답 raw 텍스트 500자 절단 / 실패 사유

#### `PUT /api/v1/settings/telemetry-config`
신호 + 가정값 일괄 저장. **payload에 없는 기존 신호 row는 자동 삭제** (replace-set semantics).

**Query parameters (required)**
| name | type | 설명 |
|---|---|---|
| `confirm` | string | 반드시 `"APPLY_CONFIG"` 문자열 (의도치 않은 호출 방지) |

**Request body** — `TelemetryConfigPayload`
```json
{
  "signals": [
    {
      "signal_name": "VehicleSpeed",
      "interval_seconds": 5,
      "minimum_delta": null,
      "resend_interval_seconds": null,
      "enabled": true,
      "display_order": 1
    }
  ],
  "cost_per_record_usd": 0.0001,
  "assumed_active_hours_per_day": 5.0,
  "assumed_vehicle_count": 10
}
```

**검증 규칙**
- `signals`: `min_length=1` — 빈 배열 거부 (Tesla가 빈 fields config 거부함)
- `signals[*].signal_name`: `^[A-Za-z][A-Za-z0-9_]*$`, 1~64자
- `signals[*].interval_seconds`: `≥ 1`
- `signals[*].resend_interval_seconds`: nullable, `≥ 0`
- `signals[*].minimum_delta`: nullable. set 시 alias 정규화 후 `NUMERIC_SIGNALS`(현재 **57개** — 2026-06-10 공식 Available Data Type=real/integer 확장분 22개 포함) 소속이어야 함 — 그 외 신호(enum/bool)면 422 (`minimum_delta는 숫자 신호에만 허용됩니다 (Tesla 공식 numeric-only): <signal_name>`)
- 같은 `signal_name` 중복 → 422 (`duplicate signal_name(s): ...`)
- (v1.8.1) alias·canonical이 **같은 canonical Field로 매핑**되는 신호를 둘 다 `enabled`로 두면 422 (`동일 canonical 신호로 매핑되는 alias 중복 — 하나만 활성화하세요: <canonical> ← <원본들>`). 예: `ChargingState`+`ChargeState` 동시 활성. `_load_signal_fields`가 `fields[canonical]`를 마지막 것으로 silent 덮어써 한쪽 설정이 유실되던 것 사전 차단(disabled 공존은 무해).
- `cost_per_record_usd`, `assumed_active_hours_per_day`: `≥ 0`
- `assumed_vehicle_count`: `int ≥ 0`

**Response 200**
```json
{ "status": "ok" }
```

**Errors**
- `412` — `confirm` 값이 `"APPLY_CONFIG"`이 아님
- `422` — Pydantic 검증 실패 (regex / 중복 / 범위 / `minimum_delta` numeric-only 위반)

**부수 효과**:
- 같은 트랜잭션에서 `payload.signals`에 없는 `telemetry_config_signals` row 모두 삭제
- 성공 후 `onboard._load_signal_fields()` 모듈 캐시 invalidate
- (2026-05-14) `asyncio.create_task(_validate_signals_against_tesla())` fire-and-forget — 첫 owner의 non-SIM 차량 1대에 push 시도 → 응답으로 신호별 `last_validation_*` 컬럼 갱신. 차량 0대 환경이면 모두 `skipped`. 운영자는 다음 GET에서 ✓/✗/⚠ 배지로 결과 확인.

#### `POST /api/v1/settings/repush-all`
저장된 모든 owner의 차량에 fleet_telemetry_config 재push.

**Query parameters (required)**
| name | type | 설명 |
|---|---|---|
| `confirm` | string | 반드시 `"REPUSH_ALL"` |

**Response 200**
```json
{
  "status": "ok",
  "summary": {
    "success_count": 4,
    "failure_count": 1,
    "needs_pairing_count": 1,
    "limit_reached_count": 0,
    "skipped_count": 0,
    "invalid_signal_count": 2
  },
  "successes": ["5YJ...A", "5YJ...B"],
  "failures": [
    { "vin": "5YJ...D", "error": "401: <Tesla 응답 body 일부>" }
  ],
  "needs_pairing": [
    { "vin": "5YJ...C", "tesla_response": "..." }
  ],
  "limit_reached": [],
  "pairing_url": "https://tesla.com/_ak/sphere.tesla.modapl.dev",
  "skipped": [
    { "owner_id": "...", "reason": "token error: No token for owner_id=..." }
  ],
  "invalid_signals": ["FooBar", "BazQux"]
}
```

배열별 shape:
- `successes`: `string[]` (vin only)
- `failures`: `[{ vin, error }]` — `error`는 `"{status_code}: {raw_response_text[:200]}"` 또는 task exception 메시지
- `needs_pairing`: `[{ vin, tesla_response }]` — `tesla_response`는 raw 응답 200자 절단
- `limit_reached`: `[{ vin, tesla_response }]`
- `skipped`: `[{ owner_id, reason }]` — owner 토큰 / products 호출 실패
- (2026-05-14) `invalid_signals`: `string[]` — 모든 차량 응답(failures + limit_reached) 텍스트를 `parse_invalid_signals`로 분석해 추출한 Tesla가 거부한 신호명 union (sorted, deduped). `summary.invalid_signal_count = len(invalid_signals)`. frontend는 이 list로 form row에 빨간 ⚠ 표시 + 배너 노출

**Errors**
- `412` — `confirm` 토큰 불일치
- `429` — 최근 300초(5분) 내 다른 repush 호출 있음. detail에 잔여 초 포함
- `500` — `TESLA_TELEMETRY_CA_CERT_B64` 미설정 등

**동작 상세**
- `SIM-`로 시작하는 VIN은 자동 skip (`skipped` 배열에는 누적 안 됨 — 카운트 누락 의도된 단순화)
- VIN 단위 push는 asyncio.gather + Semaphore(5)로 병렬

---

### 3.7 시뮬레이터 (`/api/v1/admin/sim`)

`SIM-` VIN의 가상 차량으로 telemetry 데이터 생성. 실 운영용 아님.

#### `POST /api/v1/admin/sim/start`
sim run 생성 + asyncio task 실행.

**Request body** — `SimRunCreate`
```json
{
  "vins": ["SIM-ABC123"],
  "speed_multiplier": 1.0,
  "interval_seconds_override": 30,
  "scenario": "driving",
  "include_alerts": false,
  "duration_seconds": 0,
  "name": "demo run",
  "signal_set": "default"
}
```

**검증 규칙**
- `vins`: `min_length=1, max_length=20`. 각 VIN은 `^SIM-[A-Z0-9\-]{1,13}$` (총 길이 ≤17). 중복 자동 제거.
- `speed_multiplier`: `0 <` value `≤ 100.0`, default `1.0`
- `interval_seconds_override`: nullable int, `1 ~ 86400`. **2026-05-14 신규 (Alembic 0020)**. set 시 모든 활성 신호가 N초마다 1회 전송 (per-signal interval 무시, speed_multiplier도 무시). 우선 적용. `null` 시 기존 speed_multiplier 흐름 (역호환).
- `scenario`: `"driving" | "charging" | "idle" | "mixed"`, default `"driving"`
- `include_alerts`: bool, default `false`
- `duration_seconds`: `0 ~ 86400` (24h), default `0` (=무제한)
- `name`: nullable, ≤64자
- `signal_set`: `"default" | "rich"`, default `"default"` (`rich`는 52개 신호를 5초마다 강제 전송)

**Response 200**
```json
{
  "status": "started",
  "run": { /* SimRun row dict, status=pending */ }
}
```

**Errors**
- `422` — 검증 실패 (VIN 형식 / scenario / signal_set)
- `429` — 동시 실행 cap `5` 초과

#### `POST /api/v1/admin/sim/stop/{run_id}`
asyncio task cancel + DB `status='stopped'` 마킹.

**Path parameters**
| name | type | 설명 |
|---|---|---|
| `run_id` | UUID | start에서 반환된 run.id |

**Response 200**
- 진행 중인 run: `{ "status": "stopping", "run_id": "..." }`
- 이미 종료된 run: `{ "status": "noop", "current": "<현재 status>" }`

**Errors**
- `404` — `run_id` 없음

#### `GET /api/v1/admin/sim/runs`
최근 runs 목록 (created_at DESC).

**Query parameters**
| name | type | default | 제약 |
|---|---|---|---|
| `limit` | int | `20` | `1~200` |

**Response 200**
```json
{
  "runs": [ /* SimRun row dict 배열 */ ]
}
```

각 row 형식 → [4. 데이터 모델 / `SimRun`](#4-데이터-모델).

#### `GET /api/v1/admin/sim/runs/{run_id}`
단일 run 상세.

**Response 200** — SimRun row dict (위 schema와 동일)

**Errors**
- `404` — 없음

#### `GET /api/v1/admin/sim/data-summary`
SIM 차량 + 연관 데이터 통계 (삭제 전 미리보기).

**Response 200**
```json
{
  "sim_vehicle_count": 2,
  "telemetry_events_count": 12345,
  "vehicle_alerts_count": 67,
  "active_sim_runs": 0,
  "safe_to_delete": true
}
```

#### `DELETE /api/v1/admin/sim/vehicles`
모든 `is_simulated=true` 차량 삭제. `telemetry_events` + `vehicle_alerts`도 함께 삭제.

**Query parameters (required)**
| name | type | 설명 |
|---|---|---|
| `confirm` | string | 반드시 `"DELETE_ALL_SIM"` |

**삭제 대상 events/alerts가 0건 → `200 OK`** (동기): 차량만 FK CASCADE로 삭제.
```json
{
  "status": "ok",
  "deleted_vehicles": 2,
  "cascade_deleted_events": 0,
  "cascade_deleted_alerts": 0
}
```

**비-0건 → `202 Accepted`** (v1.6.3 audit): 대용량 sim 데이터(24h·고속 run·`interval_seconds_override=1`이면 차량당 수백만 row) 동기 CASCADE 삭제가 CloudFront 30s timeout(504) + PG long-tx/lock 잔존을 유발 → `202` + `job_id` 즉시 반환 후 background task(`_do_delete_all_sim_vehicles_background`)가 events·alerts·vehicles를 명시적으로 DELETE. frontend는 `GET /admin/seed/delete-jobs/{job_id}` polling(seed 삭제와 동일 endpoint, `bulk-sim:` prefix audit). 완료 시 vehicles 목록 캐시 무효화.
```json
{
  "status": "started",
  "job_id": "8e3f...uuid",
  "expected_events": 12345,
  "expected_alerts": 67,
  "message": "sim 차량 삭제 작업이 백그라운드에서 시작되었습니다. job_id로 진행 상태를 polling 하세요."
}
```

**Errors**
- `412` — `confirm` 토큰 불일치 (`"의도치 않은 삭제 방지 — ?confirm=DELETE_ALL_SIM 쿼리 파라미터 필수"`)
- `409` — 활성 sim run 있음 (`"활성 sim run {N}개 — 모두 정지 후 다시 삭제 시도하세요"`) · 또는 비-0건 async 시작 시 다른 일괄 sim 삭제가 `in_progress`(빠른 더블클릭/동시 삭제, `_resolve_or_reject_in_flight`로 stale 초과 시 자가복구)
- `429` — 최근 300초 내 **sim** 삭제 이력 있음 (`"최근 300초 내 sim 삭제 이력 있음 (audit_id={uuid}). {wait}초 후 다시 시도하세요"`) — 2026-06-10: seeded/seeded-month/ingested 삭제 이력은 cooldown에서 제외(sim 외 경로 오차단 해소), in_progress row도 제외(in-flight 409가 담당)

**부수 효과**: `sim_delete_events` audit row 추가 (`source="api"`). 0건 동기 경로는 같은 트랜잭션에 완료 row, 비-0건 async 경로는 시작 시 `status="in_progress"` + `note="bulk-sim:all"` row INSERT → background 완료 시 `status="completed"` + 실 rowcount 기록.

#### `GET /api/v1/admin/sim/delete-events`
SIM 삭제 audit 이력 (deleted_at DESC).

**Query parameters**
| name | type | default | 제약 |
|---|---|---|---|
| `limit` | int | `20` | `1~200` |

**Response 200**
```json
{
  "events": [
    {
      "id": "...",
      "deleted_at": "2026-05-13T10:00:00+00:00",
      "deleted_vehicles": 2,
      "cascade_deleted_events": 12345,
      "cascade_deleted_alerts": 67,
      "source": "api",
      "note": null
    }
  ]
}
```

`source`: `"api"` (HTTP DELETE) 또는 `"script"` (CLI 도구).

---

## 4. 데이터 모델

Pydantic 응답 schema 정의. 출처: `backend/app/schemas.py`.

### `VehicleSummary`

| field | type | nullable | 설명 |
|---|---|---|---|
| `id` | UUID | no | — |
| `vin` | string | no | 17자 (실), `SIM-...` (시뮬) |
| `display_name` | string | no | — |
| `model` | string | no | 예: `"Model 3"` |
| `color` | string | yes | — |
| `software_version` | string | yes | 예: `"2026.4.2"` |
| `is_simulated` | bool | no | default `false` |
| `data_source` | enum | no | `live`/`seeded`/`simulated`, default `live` (`is_simulated=true` ↔ `simulated`) |
| `customer_id` | UUID | yes | 고객사 PK. `null` = 미배정 (Alembic 0030) |
| `created_at` | datetime | no | UTC ISO 8601 |
| `updated_at` | datetime | no | UTC ISO 8601 |

### `VehicleListItem` extends `VehicleSummary`

| field | type | nullable | 설명 |
|---|---|---|---|
| `event_count` | int | no | default `0` |
| `earliest_timestamp` | datetime | yes | events 0건이면 `null` |
| `latest_timestamp` | datetime | yes | — |
| `latest_telemetry` | dict | yes | carry-forward snapshot 인라인(메인 현황 N+1 제거). lat/lng 누락 시 `telemetry_events` DISTINCT ON fallback으로 좌표 보충 |
| `customer_id` | UUID | yes | 고객사 PK. `null` = 미배정 (Alembic 0030) |

### `TelemetryEventOut`

| 그룹 | field 목록 |
|---|---|
| 식별 | `id`(UUID), `vehicle_id`(UUID), `timestamp`(datetime) |
| 위치 | `latitude`, `longitude`, `altitude_m` |
| 주행 | `speed_kph`, `heading_deg`, `gear`(str), `odometer_km`, `power_w` |
| 배터리 | `battery_level`, `usable_battery_level`, `battery_range_km`, `est_battery_range_km`, `battery_heater_on`(bool) |
| 충전 | `charge_state`(str), `charging_power_kw`, `charge_amps`, `charge_limit_soc`, `charger_voltage_v`, `charger_actual_current_a`, `charge_port_door_open`(bool), `fast_charger_present`(bool), `fast_charger_type`(str), `time_to_full_charge_hours` |
| 공조 | `inside_temp_c`, `outside_temp_c`, `is_climate_on`(bool), `is_preconditioning`(bool), `driver_temp_setting_c`, `passenger_temp_setting_c`, `defrost_mode`(str), `climate_keeper_mode`(str) |
| TPMS | `tpms_pressure_fl/fr/rl/rr`, `tpms_hard_warning_fl/fr/rl/rr`(bool) |
| 차량 상태 | `locked`(bool), `sentry_mode`(bool), `vehicle_state`(str) |
| 팩 | `pack_voltage_v`, `pack_current_a`, `lifetime_energy_used_kwh`, `energy_remaining_kwh`, `isolation_resistance_ohm`, `rated_range_km`, `ideal_battery_range_km` |
| v3 promote | `longitudinal_acceleration`, `lateral_acceleration`, `pedal_position_pct`, `brake_pedal_pos_pct`, `motor_speed_rear_rpm`, `motor_torque_rear_nm` |
| Powershare (0023) | `powershare_status`(str), `powershare_type`(str), `powershare_stop_reason`(str), `powershare_hours_left`(float), `powershare_instantaneous_power_kw`(float) — 실데이터 invalid 多, 시뮬레이터 idle 시나리오 active 값 |
| raw | `raw_data` (dict, nullable) |

타입 표기 안 한 컬럼은 모두 `float | None`. 식별 3개를 제외한 모든 컬럼은 nullable.

### `VehicleAlertOut`

| field | type | nullable | 설명 |
|---|---|---|---|
| `id` | UUID | no | — |
| `vehicle_id` | UUID | no | — |
| `name` | string | no | Tesla alert 이름 |
| `started_at` | datetime | no | alert 시작 |
| `ended_at` | datetime | yes | `null` = 진행 중 또는 종료 미상(Tesla 응답이 종종 누락) |
| `audiences` | string[] | no | default `[]`. 예: `["Customer", "Service"]` |
| `received_at` | datetime | no | backend 수신 시각 |
| `raw_data` | dict | yes | 원본 Tesla alert payload |

### `SimRun` (POST start / GET runs 응답)

| field | type | 설명 |
|---|---|---|
| `id` | string(UUID) | — |
| `name` | string\|null | — |
| `vins` | string[] | — |
| `speed_multiplier` | float | — |
| `interval_seconds_override` | int\|null | set 시 모든 신호 N초마다 전송(`speed_multiplier` 무시), `null` = 기본 흐름 |
| `scenario` | string | `driving`/`charging`/`idle`/`mixed` |
| `include_alerts` | bool | — |
| `duration_seconds` | int | `0` = 무제한 |
| `signal_set` | string | `default`/`rich` |
| `status` | string | `pending`/`running`/`stopped`/`completed`/`failed`/`interrupted` |
| `started_at` | string(ISO)\|null | — |
| `stopped_at` | string(ISO)\|null | — |
| `messages_sent` | int | — |
| `errors_count` | int | — |
| `last_error` | string\|null | — |
| `created_at` | string(ISO) | — |
| `updated_at` | string(ISO) | — |

### `TelemetryConfigPayload` (PUT body 전체)

| field | type | 제약 | default | 설명 |
|---|---|---|---|---|
| `signals` | `SignalConfigIn[]` | `min_length=1` | (required) | 빈 배열 거부 |
| `cost_per_record_usd` | float | `≥ 0` | (required) | 기록 1건당 단가 |
| `assumed_active_hours_per_day` | float | `≥ 0` | (required) | 비용 추정용 가정 |
| `assumed_vehicle_count` | int | `≥ 0` | (required) | 비용 추정용 가정 |

추가 검증: `signals`의 `signal_name`이 중복되면 422 (`duplicate signal_name(s): ...`).

### `SignalConfigIn` (`TelemetryConfigPayload.signals` 항목)

| field | type | 제약 | default |
|---|---|---|---|
| `signal_name` | string | `^[A-Za-z][A-Za-z0-9_]*$`, 1~64자 | (required) |
| `interval_seconds` | int | `≥ 1` | (required) |
| `minimum_delta` | float\|null | 숫자 신호에만 허용 (Tesla numeric-only) — alias 정규화 후 `NUMERIC_SIGNALS`(현재 **57개**, 2026-06-10 확장) 외 신호(enum/bool)에 set 시 422 | `null` |
| `resend_interval_seconds` | int\|null | `≥ 0` | `null` |
| `enabled` | bool | — | `true` |
| `display_order` | int | — | `0` |

### `SimRunCreate` (POST /admin/sim/start body)

| field | type | 제약 | default |
|---|---|---|---|
| `vins` | string[] | `min_length=1, max_length=20`, 각 항목 `^SIM-[A-Z0-9\-]{1,13}$` (총 ≤17자), 중복 자동 제거 | (required) |
| `speed_multiplier` | float | `0 <` value `≤ 100.0` | `1.0` |
| `scenario` | string | `"driving" | "charging" | "idle" | "mixed"` | `"driving"` |
| `include_alerts` | bool | — | `false` |
| `duration_seconds` | int | `0 ~ 86400` | `0` (=무제한) |
| `name` | string\|null | ≤64자 | `null` |
| `signal_set` | string | `"default" | "rich"` | `"default"` |
| `interval_seconds_override` | int\|null | `1 ~ 86400` | `null` (=`speed_multiplier` 흐름) — set 시 모든 신호 N초마다 1회 전송(`speed_multiplier` 무시) |

### `CustomerUpdate` (PATCH /customers/{id} body)

| field | type | 제약 | default |
|---|---|---|---|
| `name` | string | `min_length=1, max_length=64` (공백만이면 422) | (required) |

응답은 `CustomerSummary`(vehicle_count 포함). 변경 없는 동일 이름이면 noop으로 200. 에러: `404`(없는 customer_id) · `409`(이미 존재하는 이름, UNIQUE 위반) · `422`(name 검증 실패).

---

### 3.8 Seed 관리 (`/api/v1/admin/seed`) — Alembic 0019/0020/0022

외부 dump 데이터를 S3에서 RDS로 적재 + 차량별/월별 삭제 + 월별 비교. 모든 endpoint는 `data_source='seeded'` 차량만 다룸 — `live`/`simulated`는 자동 격리.

#### `DELETE /api/v1/admin/seed/vehicles/{vehicle_id}` (2026-05-15 async background job, Alembic 0022 / M3)
seeded 차량 1대 + 연관 events/alerts 삭제.

**큰 차량 (>30s) → CloudFront 504 회피**: 1.4M+ row 단일 차량 CASCADE DELETE도 timeout 위험. 0건이 아니면 `202 Accepted` + `job_id` 반환 후 background task로 실 DELETE. frontend는 `GET /admin/seed/delete-jobs/{job_id}` polling (월별 삭제와 동일 endpoint).

**Query parameters (required)**
| name | type | 설명 |
|---|---|---|
| `confirm` | string | 반드시 `"DELETE_SEEDED"` |

**Response — 두 가지 status code**

`200 OK`, `status="ok"` (events+alerts 모두 0건 — 동기 처리):
```json
{
  "status": "ok",
  "vehicle_id": "...",
  "vin": "5YJ...",
  "deleted_events": 0,
  "deleted_alerts": 0
}
```

`202 Accepted`, `status="started"` (비-0건, background job 시작):
```json
{
  "status": "started",
  "job_id": "...",
  "vehicle_id": "...",
  "vin": "5YJ...",
  "expected_events": 1426619,
  "expected_alerts": 200,
  "message": "차량 삭제 작업이 백그라운드에서 시작되었습니다. job_id로 진행 상태를 polling 하세요."
}
```

**Errors**
- `404` — 차량 없음
- `409` — `data_source != 'seeded'` (live/simulated 거부) 또는 다른 차량별 삭제 job이 `in_progress`
- `412` — confirm 토큰 불일치
- `429` — 60초 cooldown

**부수 효과**: 비-0건은 `sim_delete_events`에 `status='in_progress'` row INSERT(`note='seeded:VIN'`). background 완료 시 `status='completed'` + `deleted_vehicles=1` + `cascade_deleted_*` rowcount 기록.

#### `DELETE /api/v1/admin/seed/events?year=&month=[&vehicle_id=]` (2026-05-15 async background job, Alembic 0022)
seeded 차량의 [year-month] events + alerts 삭제. 차량 row는 보존.

**큰 월 (>30s) → CloudFront 504 회피**: 비-0건이면 즉시 `202 Accepted` + `job_id` 반환 후 background task로 실 DELETE 수행. frontend는 `GET /admin/seed/delete-jobs/{job_id}` polling으로 진행 확인.

**Query parameters**
| name | type | required | 설명 |
|---|---|---|---|
| `year` | int | ✅ | 2020~2100 |
| `month` | int | ✅ | 1~12 |
| `vehicle_id` | UUID | optional | 지정 시 그 차량만, 미지정 시 모든 seeded 차량 |
| `confirm` | string | ✅ | `"DELETE_SEEDED_MONTH"` |

**Response — 두 가지 status code**

`200 OK`, `status="noop"` (해당 범위 데이터 0건, 에러 아님):
```json
{
  "status": "noop",
  "month": "2026-05",
  "vehicle_id": null,
  "deleted_events": 0,
  "deleted_alerts": 0,
  "message": "해당 범위에 삭제할 seeded 데이터가 없습니다."
}
```

`202 Accepted`, `status="started"` (비-0건, background job 시작):
```json
{
  "status": "started",
  "job_id": "8e3f...uuid",
  "month": "2026-09",
  "vehicle_id": null,
  "expected_events": 1426619,
  "expected_alerts": 434799,
  "message": "삭제 작업이 백그라운드에서 시작되었습니다. job_id로 진행 상태를 polling 하세요."
}
```

**Errors**:
- `412` — confirm 토큰 불일치
- `429` — 60s cooldown (직전 월별 삭제 후 60초 내)
- `409` — vehicle_id가 live/simulated 또는 다른 월별 삭제 job이 in_progress
- `404` — vehicle_id 차량 없음

**부수 효과**: 시작 시 `sim_delete_events`에 audit row 1개 INSERT(`status='in_progress', cascade_*=0, note='seeded-month:YYYY-MM[:vehicle_id]'`). background 완료 시 status='completed' + 실 카운트 update. 실패 시 status='failed' + error 채움. 응답 후 monthly-overview cache invalidate (실제 invalidate는 background 종료 시점).

#### `GET /api/v1/admin/seed/delete-jobs/{job_id}` (2026-05-15 신규, Alembic 0022)
월별 삭제 background job 진행 상태 조회. frontend polling(2초 간격) 권장.

**Path parameters**
| name | type | 설명 |
|---|---|---|
| `job_id` | UUID | `DELETE /admin/seed/events`·`/vehicles/{id}` · `DELETE /admin/sim/vehicles`(bulk-sim) · `DELETE /admin/bronze-replay/ingested-vehicles/{id}`의 202 응답 `job_id` (= sim_delete_events.id) |

**Response 200**
```json
{
  "job_id": "8e3f...uuid",
  "status": "completed",
  "deleted_events": 1426619,
  "deleted_alerts": 434799,
  "started_at": "2026-05-15T09:30:00+00:00",
  "finished_at": "2026-05-15T09:31:42+00:00",
  "error": null,
  "note": "seeded-month:2026-09"
}
```

`status` 값:
- `in_progress` — background 작업 중. polling 계속
- `completed` — 정상 완료. `deleted_events`/`deleted_alerts`에 실 카운트
- `failed` — 예외 발생. `error` 필드 채움 (500자 절단)
- (legacy) — 0022 이전 audit row는 status NULL이지만 응답에서는 `"completed"`로 fallback (호환)

valid `note` prefix(그 외 prefix는 404): `seeded-month:`(월별) · `seeded:`(차량별) · `ingested:`(Bronze replay 적재분) · `bulk-sim:`(일괄 sim 삭제, v1.6.3).

**Errors**: 404 (job_id 없음 / 위 valid prefix 외 audit row).

#### `POST /api/v1/admin/seed/ingest-one?s3_key=&confirm=SCAN_S3` (2026-05-14 신규)
단일 S3 파일 적재 — frontend가 파일별 progress bar 표시용. Idempotent.

**Query parameters (required)**
| name | type | 설명 |
|---|---|---|
| `s3_key` | string | `dumps/` 또는 `topics/` prefix로 시작해야 함 |
| `confirm` | string | `"SCAN_S3"` |

**Response 200**
- 정상: `{status: "completed", s3_key, event_count, alert_count, vehicle_count, file_size_bytes, vins[]}`
- 이미 적재됨: `{status: "already_loaded", s3_key, event_count, loaded_at}`

**Errors**: 400 (prefix 외부) / 412 / 502 (S3 오류) / 500 (적재 오류)

#### `GET /api/v1/admin/seed/monthly-overview` (2026-05-14 신규)
S3 `topics/<topic>/year=YYYY/month=MM/` vs DB seeded 카운트 월별 비교.

**600초 TTL 캐시** (env `SEED_OVERVIEW_CACHE_TTL`, asyncio.Lock stampede 방지). ingest/delete 후 자동 invalidate.

> ⚠️ DB 월별 집계(date_trunc GROUP BY)에 `statement_timeout=45s`를 둔다(R1 감사). functional index(0033)를 못 타는 풀스캔이 cache lock을 장시간 점유해 동시 '데이터 현황' 요청을 직렬 차단하던 것을 방지 — 초과 시 **503**(`telemetry_events` `ANALYZE` 후 재시도). 캐시는 미갱신(다음 호출 재시도).

**Response 200**
```json
{
  "months": [
    {
      "year": 2025, "month": 11,
      "s3": {
        "tesla_V": {"file_count": 966, "size_bytes": 184433153},
        "tesla_alerts": {"file_count": 609, "size_bytes": 5348501},
        "total_files": 1575,
        "total_size_bytes": 189781654
      },
      "db": {"event_count": 434799, "alert_count": 352},
      "status": "loaded"
    }
  ],
  "topics_prefix": "topics/",
  "topics_ingested": ["tesla_V", "tesla_alerts"]
}
```

`status`:
- `loaded` — DB event_count > 100
- `loadable` — DB 0 + S3에 파일 있음
- `partial` — DB 일부만
- `db_only` — DB에만 있음, S3 없음

#### `GET /api/v1/admin/seed/list-month-files?year=&month=` (2026-05-14 신규)
특정 월의 모든 S3 file keys 반환 — frontend가 ingest-one을 순차 호출하기 위함.

**Response 200** `{year, month, total_files, already_loaded, to_load: string[]}`

`to_load`: `seed_imports` 테이블에 없는 keys만 — frontend가 이 list를 progress bar로 순회.

#### `GET /api/v1/admin/seed/imports?limit=&status=`
적재 audit 이력 (loaded_at DESC).

`status` query: `"completed" | "failed" | None` (필터).

**Response 200** `{imports: [{s3_key, loaded_at, vehicle_id, event_count, file_size_bytes, status, last_error}]}`

---

### 3.9 Bronze Replay (`/api/v1/admin/bronze-replay`) — Alembic 0035 (v1.5.8 Phase B)

기존 `backend/scripts/replay_s3_to_kafka.py` CLI 도구를 admin UI로 노출. **워크플로우**: S3 `topics/` → Kafka → kafka_consumer가 DB 적재 + s3-archiver가 Bronze envelope dual-publish → Iceberg Sink Parquet 적재.

SeedManager(0019, S3 dumps/ → DB 직접 적재)와 별개 워크플로우. `/admin/seed` 화면 하단에 BronzeReplayManager 추가.

#### `GET /api/v1/admin/bronze-replay/preview?prefix=topics/...`
S3 prefix 미리보기. `paginator.paginate()`로 전체 카운트 (큰 prefix 1-3초).

**Query**: `prefix` (str, min 1 max 512, `topics/` prefix 필수, 400 reject)

**Response 200** `BronzeReplayPreview`:
```json
{
  "prefix": "topics/tesla_V/year=2025/",
  "object_count": 17824,
  "total_bytes": 1234567890,
  "first_key": "topics/tesla_V/year=2025/month=01/day=01/...",
  "last_key": "topics/tesla_V/year=2025/month=12/day=31/...",
  "sample_keys": ["...up to 5..."],
  "omitted_topics": [{ "topic": "tesla_alerts", "object_count": 312 }]
}
```

> **`omitted_topics`**: 단일 **저장 토픽** prefix(예: `topics/tesla_V/year=2025/`)가 같은 기간(rest)의 다른 저장 토픽(`tesla_V`/`tesla_alerts`) 형제를 빠뜨릴 때 경고용 배열(`{topic, object_count}`). 비어 있으면 누락 없음. `topics/`(전체)·비-저장 토픽 prefix면 항상 `[]`. `object_count`는 cap(100000)에서 절단될 수 있음. (예: `tesla_V`만 리플레이하면 `tesla_alerts`가 누락 → 차량 알림 빈 화면 — `alerts_ingest_gap` 재발 방지.)

#### `POST /api/v1/admin/bronze-replay/start`
replay 시작 — `replay_imports` row 생성 + `asyncio.create_task(_run_replay)` background.

**Body** `BronzeReplayCreate`:
```json
{
  "prefix": "topics/tesla_V/year=2025/",
  "rate_limit": 500,        // 1~5000 msg/s
  "max_objects": null,      // 테스트용 cap (1~100000)
  "allow_partial": false    // 토픽 누락 가드 우회(기본 false)
}
```

**가드**:
- `prefix`는 `topics/`로 시작해야 함 (400)
- 같은 prefix에 `status IN ('pending','running')` 이미 존재 시 **409** (Kafka 중복 publish 회피 — fast-path SELECT count + `uq_replay_imports_prefix_active` 부분 UNIQUE 인덱스(0036) IntegrityError로 원자적 차단)
- **토픽 누락 가드(409)**: `allow_partial=false`(기본)일 때 단일 저장 토픽 prefix(예: `topics/tesla_V/...`)가 같은 기간의 형제 저장 토픽(`tesla_alerts`)을 S3에 두고 누락하면 **409로 차단**(silent 누락 → 알림 빈 화면 방지). 모두 적재하려면 prefix를 `topics/`로, 이 토픽만 적재하려면 `allow_partial=true`로 재요청.

**Response 200** `BronzeReplayStatus` (초기 status='pending').

Background task 동작:
1. S3 keys 전체 `asyncio.to_thread`로 미리 fetch (event loop 차단 회피)
2. `replay_imports.total_objects` 갱신 + `status='running'`
3. AIOKafkaProducer start (`client_id=teslafleet-bronze-replay-{id}`)
4. keys iterate + `get_object` (to_thread) + JSONL split + throttle + `producer.send`
5. 5초마다 progressive UPDATE (`processed_objects`/`total_lines`/`published_lines`/`errors`)
6. 완료 시 `status='completed'` + `finished_at`. 실패 시 `'failed'` + `error_message`. cancel 시 `'stopped'`.

#### `GET /api/v1/admin/bronze-replay/list?limit=N`
이력 (최신순). `limit` 1~200, default 50.

**Response 200** `{items: BronzeReplayStatus[], total: int}`

#### `GET /api/v1/admin/bronze-replay/{id}`
단건 실시간 status. UI polling 용 (5초/30초).

**Response 200** `BronzeReplayStatus` / 404 not found.

#### `POST /api/v1/admin/bronze-replay/{id}/stop`
running task cancel + `status='stopped'`. running 메모리 task만 cancel 가능 (process 재시작 후엔 dangling은 lifespan에서 별도 정리).

**Response 200** `BronzeReplayStatus` / 404 / 409 (이미 종료된 row).

#### `DELETE /api/v1/admin/bronze-replay/{id}` — v1.6.0
replay 실행 **이력 row(`replay_imports`)** 삭제. 적재 데이터(telemetry_events / Iceberg Bronze)는 **건드리지 않음** — 이력만 정리.

**가드**: `status IN ('pending','running')`이면 **409** (먼저 `/stop` 후 삭제). completed/failed/stopped만 삭제 가능.

**Response 200** `{"deleted": "<uuid>", "status": "deleted"}` / 404 / 409.

> Bronze Iceberg에 적재된 replay 데이터까지 지우려면 `glue/sql/replay_bronze_cleanup.sql`
> (Athena `DELETE FROM teslafleet_bronze_dev.telemetry_raw WHERE event_time BETWEEN ...`,
> **AWS 작업·승인 필요**) 참조. event_time(원본 createdAt) 범위로 replay prefix 기간을 지정.

#### `GET /api/v1/admin/bronze-replay/ingested-vehicles` — v1.6.1
적재된 차량 목록(replay/실시간 무관). Bronze Replay 화면의 '적재 차량 삭제' UI용. 정적 경로라 `/{replay_id}` GET보다 먼저 등록.

**Response 200** `{"items": [{"id","vin","data_source","event_count","last_event_at"}], "total": N}`

#### `DELETE /api/v1/admin/bronze-replay/ingested-vehicles/{id}?confirm=DELETE_INGESTED` — v1.6.1
적재 차량 1대 + 연관 `telemetry_events`/`vehicle_alerts` **cascade 삭제**. seeded 전용 삭제(`live`는 409)와 달리 **data_source 무관** — replay가 `live`로 분류한 Tesla 형식 데이터를 정리.

**가드**: `confirm=DELETE_INGESTED` 필수(412), 404, **409**(다른 `ingested:` 차량 삭제 job이 `in_progress` — `_resolve_or_reject_in_flight(note prefix='ingested:')`, 빠른 더블클릭/동시 삭제 방지. stale 초과 시 자가복구).

**대용량 504 회피 (v1.6.1 audit)**: replay 적재분은 차량당 수백만 행 → 요청 경로 동기 cascade 삭제 시 CloudFront 30s timeout(504). 따라서 seed 차량 삭제와 동일한 async 패턴 적용:
- **0건 → 동기 `200`** `{"status":"ok","deleted","vin","telemetry_events":0,"vehicle_alerts":0}`
- **비-0건 → `202 Accepted`** `{"status":"started","job_id","vin","expected_events","expected_alerts","message"}` 반환 후 background task로 실 DELETE. frontend는 `GET /admin/seed/delete-jobs/{job_id}` polling(seed 삭제와 동일 endpoint, `ingested:` prefix audit). 완료 시 vehicles 목록 캐시 무효화.

(Iceberg Bronze는 위 `replay_bronze_cleanup.sql`로 별도.)

---

### 3.10 Kafka lag 모니터 (`/api/v1/admin/kafka-lag`) — v1.5.8 Phase B

'데이터 현황'(/admin/data-status) status card용. 모든 consumer group의 lag을 한 번에 조회. 10초 in-memory cache.

#### `GET /api/v1/admin/kafka-lag?no_cache=0/1`

**구현**: `aiokafka.admin.AIOKafkaAdminClient.list_consumer_group_offsets` + `AIOKafkaConsumer.end_offsets`. 모니터 group 3종:
- `teslafleet-backend-consumer` (DB INSERT)
- `teslafleet-s3-archiver` (S3 archive + Bronze envelope dual-publish)
- `connect-teslafleet-bronze-telemetry-raw` (Iceberg sink)

**Query**: `no_cache` (0 default, 1이면 cache bypass)

**Response 200**:
```json
{
  "groups": [
    {
      "group_id": "teslafleet-backend-consumer",
      "topics": [
        {"topic": "tesla_V",
         "partitions": [{"partition": 0, "committed": N, "end_offset": M, "lag": L}, ...],
         "lag_total": ...}
      ],
      "lag_total": ...
    },
    ...
  ],
  "total_lag": ...,
  "cached_at": 1234567890.0
}
```

**Stale fallback**: broker 호출 실패 + 직전 cache 있으면 → `stale: true`, `error: "..."` 함께 반환 (502 회피).

---

### 3.11 Lakehouse 모니터링 (`/api/v1/admin/lakehouse`) — v1.6.x

Iceberg 이후(Bronze 검증 → Silver) 운영 가시성. '데이터 현황'(/admin/data-status) 카드(GlueRunsCard / DataQualityCard)용. 인증: `X-Admin-Key`.

#### `GET /api/v1/admin/lakehouse/glue-runs?no_cache=0/1`

검증·Silver Glue job의 최근 실행 현황. **`glue:GetJobRuns`만 호출 → 과금 0**, 30s TTL in-memory cache(`no_cache=1`이면 bypass). IAM은 2개 job ARN으로 한정.

**Response 200**:
```json
{ "jobs": [ { "job_name": "teslafleet-dev-bronze-contract-validation", "label": "Validation",
              "latest": { "...": "최근 run 1건" }, "recent": [ "...최근 N건..." ] } ],
  "fetched_at": 1234567890.0 }
```

#### `GET /api/v1/admin/lakehouse/dq-overview?no_cache=0/1`

Bronze Contract Validation 데이터 품질 요약(Athena 쿼리, `current_v` ROW_NUMBER). **과금 3중가드**: workgroup bytes-scanned cutoff(1GB) + 600s TTL cache + polling 없음.

**Response 200**:
```json
{ "total": 8780000, "pass": 8780000, "fail": 0, "error": 0, "pass_rate": 1.0,
  "top_failures": [ { "failure_code": "...", "count": 0 } ], "fetched_at": 1234567890.0 }
```

**Stale fallback**: Athena 호출 실패 + 직전 cache 있으면 → `stale: true` 함께 반환.

#### `GET /api/v1/admin/lakehouse/pipeline-status` — v1.6.6

Lakehouse 파이프라인(validation+silver EventBridge Scheduler)의 ON/OFF 상태 + 주기. '데이터 현황'(/admin/data-status) PipelineCard용.

**Response 200**:
```json
{ "enabled": true,
  "schedules": [ { "name": "teslafleet-dev-bronze-contract-validation", "label": "Bronze 검증",
                   "state": "ENABLED", "schedule_expression": "cron(0 * * * ? *)" } ],
  "fetched_at": 1234567890.0 }
```
`enabled`은 두 Scheduler가 **모두** ENABLED일 때만 true.

**Errors**: `502` — Scheduler 조회 실패(AWS 오류/응답 파싱 실패).

#### `POST /api/v1/admin/lakehouse/pipeline-toggle?enabled=true|false` — v1.6.6

두 EventBridge Scheduler의 state를 일괄 ENABLED/DISABLED로 변경(비용 절감 — 안 쓸 땐 OFF로 Glue 과금 ~0).
`scheduler:GetSchedule`+`UpdateSchedule`+`iam:PassRole`(scheduler 한정) IAM 사용. `_TOGGLE_LOCK`으로 동시 토글
직렬화. **부분 실패**(한쪽 update 실패) 시 이미 바꾼 쪽을 원래 state로 복원 후 **502**(한쪽만 바뀐 불일치 방지).
OFF 동안 Silver/DQ는 stale, ON 재개 시 left-anti 증분으로 self-heal. **Response 200**: `pipeline-status`와 동일 형식.

#### `GET /api/v1/admin/duplicates/overview` — v1.6.9

telemetry_events 중복 점검 상태 + 마지막 검사/정리 결과. '데이터 현황'(/admin/data-status) DuplicatesCard용(작업 중 3s 폴링).
상태는 backend in-memory(단일 컨테이너) — 재시작 시 idle로 리셋되고 마지막 결과만 사라짐(데이터 무관).

**Response 200**:
```json
{ "status": "idle",
  "result": { "scanned_at": 1234.5, "total_events": 12000000, "dup_groups": 1,
              "rows_in_dup_groups": 3, "excess_rows": 2, "exact_excess": 1,
              "collision_groups": 1, "truncated": false, "duration_s": 31.2,
              "by_vehicle": [ { "vin": "5YJ…", "display_name": "…", "dup_groups": 1, "excess": 2 } ] },
  "cleanup": { "deleted": 1, "truncated": false, "finished_at": 1234.9, "duration_s": 5.0 },
  "error": null,
  "progress": null }
```
`progress`는 **작업 중에만** non-null — `{ "stage": "scanning|deleting|rescanning", "deleted": int,
"total": int|null, "scanned": int|null, "scan_total": int|null, "started_at": epoch }`. deleting(청크)은
윈도우 커밋마다 갱신: 진행바는 `scanned`/`scan_total`(스캔 위치 — 중복이 후반에 몰려도 부드럽게 진행),
`deleted`는 누적 삭제 수. rescanning은 정리 후 자동 재검사 구간.
`result.truncated`는 scan이 `_MAX_BATCHES`(윈도우 수 안전망) 도달로 부분 집계됐는지(cleanup.truncated와 대칭, 정상 운영선 false).

#### `POST /api/v1/admin/duplicates/scan` — v1.6.9

중복 검사 시작 — **백그라운드 태스크**(즉시 `{"status":"scanning"}` 반환, 진행은 overview 폴링).
배경: telemetry_events는 (vehicle_id,timestamp) 유니크 제약이 없어 Kafka at-least-once(seek-back
재시도)·replay 재실행·seed 재적재가 중복 유입 경로(나머지 테이블은 유니크 제약으로 원천 차단).
cleanup과 동일하게 **timestamp 윈도우(`_WINDOW_ROWS`=10만 행) 청크**로 키셋 이동하며 각 윈도우 내에서만
작은 GROUP BY를 수행해 Python 누적(work_mem 초과 정렬 없음 → 디스크 스필 구조적 차단). 2-phase(dup
(vehicle,ts) 그룹을 인덱스로 먼저 찾고 md5는 그 행에만)로 **exact**(payload(raw_data)까지 동일 — 재전송
산물, 삭제 대상)와 **collision**(같은 시각·다른 payload — 서로 다른 메시지, 보존)으로 분류. exact_excess는
(vehicle,ts) 그룹별 (행수 − distinct payload 수) 누적. **Errors**: `409` 이미 작업 중.

#### `POST /api/v1/admin/duplicates/cleanup?confirm=DELETE_DUPLICATES` — v1.6.9 🔴

완전중복(exact)만 제거 — **백그라운드 태스크**. 그룹마다 **keeper = typed 컬럼 non-null 최다 행(동률 시 id 최소)** 1행 보존 — raw_data가 같아도 carry-forward(consumer INSERT 시점 컬럼 채움) 때문에 재전송 사본은 sparse일 수 있어, 밀도 우선으로 정보 많은 행을 남긴다. collision은 삭제 안 함.
`DELETE … RETURNING vehicle_id`(실측 삭제 행 기준 — 동시 삭제 경로와 겹쳐도 과차감 없음) + `vehicles.event_count`(0024 비정규화) 차감을 같은 트랜잭션으로 윈도우당 커밋(중단돼도 정합 유지).
**timestamp 윈도우 청크 처리**(2026-06-11 DiskFull 사고 fix): 전체 테이블을 한 번에
GROUP BY/정렬하면 work_mem(작은 t4g.small)을 넘어 임시파일로 수 GB 스필 → **RDS 디스크 풀**
(여유 8GB→1.8GB 실측, 적재 중단 위험). 대신 `_WINDOW_ROWS`(=10만)행 단위로 timestamp 경계를
키셋 이동하며 각 윈도우 안에서만 window ranking+삭제 → 어떤 쿼리도 work_mem 초과 정렬을 하지
않아 **스필 구조적 차단**(플래너 plan 무관). 같은 (vehicle_id,timestamp) 그룹은 같은 윈도우(ts
경계 분할). 한 번의 호출로 전체 소진, 진행바는 `scanned/scan_total`(스캔 위치)로 부드럽게 진행.
안전망 `_MAX_BATCHES`(윈도우 수) 도달 시 `truncated=true`(잔여 가능, 재실행). cleanup 응답에
`rounds`(=윈도우 수) 포함. 완료 후 자동 재검사로 result 갱신.
**RDS만 정리**(S3 raw/Bronze/Silver 불변 — Silver는 자연키 dedup이라 원래 무관).
> ⚠️ 대량 삭제 중 대상 차량에 실시간 재유입(seek-back 재전송)이 활발하면 종료가 지연될 수 있음 — 저트래픽 시간대 권장. 대량 삭제 후엔 `ANALYZE telemetry_events` 권장(플래너 통계 갱신).
**Errors**: `412` confirm 누락/불일치 · `409` 이미 작업 중.

### 3.12 계정 인증 (`/api/v1/auth/account`) — v1.7.0 (Alembic 0041) · 세션 관리·보안 강화 v1.7.1 (0042)

nginx Basic auth 대체 로그인. 에러 `detail`은 **코드 문자열**(SPA가 i18n 매핑) — §5 표 아래 코드 참조.

| Method | Path | 인증 | 설명 |
|---|---|---|---|
| POST | `/auth/account/signup` | 공개 | **Manager 가입 — body `{email}`만**(사용자 명세). 비번은 디폴트 `modapl#123`, 고객사 미분배 상태로 생성(분배 전 로그인 불가). `201 {email, role}` / `409 email_exists` / `422 invalid_email` |
| POST | `/auth/account/login` | 공개 | body `{email, password}`. **MFA 미등록 계정**: 성공 시 `__Host-tf_account` 세션 쿠키(30일) + `{account}` 반환. **MFA 등록 계정(v1.7.5)**: 세션 미발급, `{mfa_required: true, mfa_token}`(단기 HMAC 챌린지) 반환 → `/login/verify-otp` 필요. `401 invalid_credentials`(계정 부재 시에도 동일 — 더미 검증으로 타이밍 균등화) / **`403 customer_not_assigned`**(manager 미분배) / **`429 account_locked`**(login_max_failures(8) 초과 지수 백오프 잠금) |
| POST | `/auth/account/login/verify-otp` | 공개 (챌린지) | **(v1.7.5)** 로그인 2단계 — body `{mfa_token, code}`(OTP 6자리 또는 백업코드). 성공 시 세션 쿠키 + `{account}`(백업코드 사용 시 `backup_codes_remaining` 포함). `401 mfa_invalid_code` / `401 mfa_code_reused`(이미 쓴 TOTP step 재사용·RFC 6238 §5.2) / `401 mfa_challenge_invalid`(토큰 만료(5분)/변조 → 재로그인) / **`403 customer_not_assigned`**(v1.8.2 — 챌린지 발급 후 admin이 고객사 분배 해제 시·login과 대칭. ⚠️ 가드가 OTP/백업코드 검증 **앞**이라 백업코드는 소모되지 않음) / `429 account_locked`(OTP 오답 누적 — 비번 단계와 카운터 공유) |
| GET | `/auth/account/mfa/setup` | **세션 필수** | **(v1.7.5)** OTP 등록 시작 — provisional secret 생성·저장(enabled=false 유지) + `{secret, otpauth_uri, issuer}`(FE가 QR 렌더). `409 mfa_already_enabled` |
| POST | `/auth/account/mfa/enable` | **세션 필수** | **(v1.7.5)** 등록 확정 — body `{code}`(setup secret의 첫 OTP). 성공 시 `mfa_enabled=true` + `{enabled, backup_codes: [10]}`(**평문 1회만** 반환·이후 해시만 저장). `401 mfa_invalid_code` / `400 mfa_setup_required`(setup 선행) / `409 mfa_already_enabled`(이미 등록 — 해제 후 재등록) |
| POST | `/auth/account/mfa/disable` | **세션 필수** | **(v1.7.5)** 본인 OTP 해제 — body `{password}`(현재 비번 재확인). secret/백업코드 제거. enforce=1이면 다음 데이터 접근 시 재등록 게이트. `400 invalid_current_password` |
| POST | `/auth/account/logout` | 쿠키(멱등) | 현재 세션 행 삭제 + 쿠키 제거. `204` |
| GET | `/auth/account/me` | 쿠키(선택) | `{account: {...}\|null, auth_enforced: bool}` — SPA AuthGate가 게이팅 판단(legacy 모드 = `null`+`false`) |
| POST | `/auth/account/password` | **세션 필수** | body `{current_password?, new_password}`. **비번 정책: ≥10자 + HIBP 유출비번 거부 + 재사용 금지 + 디폴트(`modapl#123`) 금지**. **must_change 계정은 `current_password` 불요**(이미 디폴트/리셋 비번으로 로그인해 인증 — 생략/빈 문자열 허용), 일반 계정은 필수·검증. 성공 시 must_change 해제 + 현재 세션 외 전부 revoke. `400 invalid_current_password`(일반 계정 한정) / `422 weak_password`·`pwned_password`·`password_reuse` / `401 login_required` |
| GET | `/auth/account/sessions` | 세션 | 내 활성 세션 목록(id·last_seen·user_agent·**ip_address·country·city**(0045·로그인 IP/위치)·current) — 원격 로그아웃 UI |
| DELETE | `/auth/account/sessions/{id}` | 세션 | 내 특정 세션 원격 로그아웃(본인 소유만) |
| POST | `/auth/account/sessions/revoke-others` | 세션 | 현재 외 전부 로그아웃 |

**Account 모델**: `{id, email, role: "admin"\|"manager", customer_id, customer_name, must_change_password, mfa_enabled, mfa_required}` (`/login`·`/me`의 `_account_payload`). `mfa_required`=`ACCOUNT_MFA_ENFORCE` AND 미등록(SPA 등록 게이트 강제).

### 3.13 계정 설정 (`/api/v1/admin/accounts`) — v1.7.0 (Admin 전용) · 감사로그 페이징 v1.7.1 (0042/0043)

고객사별 계정 분배 관리(사용자 명세). 라우터 전체 `require_admin_account`(admin 세션 또는 X-Admin-Key). **admin 계정은 분배/리셋/삭제 대상 아님(`400 admin_account_immutable`)** — manager 전용 관리.

| Method | Path | 설명 |
|---|---|---|
| GET | `/admin/accounts?search=` | 전체 계정 + 고객사명 — **미분배 우선 정렬**, `search`는 email 부분일치(대소문자 무시). `{accounts: [...], total, admin_count}` — `admin_count`=전역 admin 수(search 필터 무관, FE '마지막 admin 강등' 버튼 비활성 판정용·권위는 백엔드 last_admin 가드, v1.7.6). SPA가 미분배/분배/관리자 섹션 분리 렌더 |
| GET | `/admin/accounts/audit?event=&limit=&offset=` | **보안 감사로그** — login_success/fail/locked·password_change/reset·customer_assign·account_create/delete·**admin_promote/admin_demote**·session_revoke·admin_key_used·force_reset_rearm·mfa_enabled/disabled/verify_fail/backup_used/reset 등 최근순. **페이징**: `limit`(기본 **30**, ≤500)·`offset`(≥0)·`event` 필터. 정렬 `created_at DESC, id DESC`(동률 결정적 — 페이지 경계 무중복/무누락). 응답 `{entries: [{id,event,actor,target_email,detail,ip_address,country,city,created_at}], total, limit, offset}` — **(0044)** `ip_address`(원문 IP)·`country`·`city`(CloudFront viewer 위치). 미적용/시스템/구버전 행은 null. |
| PUT | `/admin/accounts/{id}/customer` | body `{customer_id: UUID\|null}` — 고객사 분배/해제(null). **변경 시 세션 revoke + 감사**. **`require_admin_session`(admin 세션 전용 — X-Admin-Key는 `403 admin_session_required`, `admin_key_block_dangerous`)**. `404 customer_not_found` |
| POST | `/admin/accounts/{id}/reset-password` | **비번 리셋: 디폴트 `modapl#123` + must_change(첫 로그인 강제 변경) + 미분배 + 세션 revoke**. `require_admin_session`. 재분배해야 로그인 가능 |
| POST | `/admin/accounts/{id}/reset-mfa` | **(v1.7.5) OTP 등록 해제**(매니저가 앱·백업코드 모두 분실 시 복구) — secret/백업코드 제거 + 세션 revoke + 감사. `require_admin_session`. **manager 한정**(admin은 `400 admin_account_immutable` — admin 본인 OTP 분실은 비상 env `ADMIN_MFA_RESET=1`로 복구) |
| POST | `/admin/accounts/{id}/role` | **(v1.7.6) 역할 승격/강등** — body `{role: "admin"\|"manager"}`. 승격(manager→admin: customer_id 해제) / 강등(admin→manager). 변경 시 세션 revoke + 감사(`admin_promote`/`admin_demote`). `require_admin_session`. **가입은 manager로만 되므로 admin 추가는 이 승격이 유일 경로.** `400 last_admin`(**마지막 admin 강등 차단** — admin 행 `FOR UPDATE`로 동시 강등 레이스 직렬화) / `422 invalid_role`. 응답 `{account, changed}` |
| DELETE | `/admin/accounts/{id}` | manager 계정 삭제(스팸 정리) — 세션 CASCADE + 감사. `require_admin_session`. `204` |

**AccountRow**: Account + `{created_at, last_login_at, must_change_password, mfa_enabled}`(GET /admin/accounts·reset-password·reset-mfa·role·customer 응답 행 — admin이 계정별 OTP 등록 현황 확인)
**AccountBrief**(v1.7.6): `{id, email}` — `CustomerDetail.accounts[]`(GET /customers/{id} admin 응답, 인라인 분배 해제용). `account_emails`(이메일만)는 호환 유지.
**부트스트랩**: backend lifespan이 admin 0명일 때 `ADMIN_EMAIL`/`ADMIN_BOOTSTRAP_PASSWORD`(.env, deploy.sh 1회 생성·보존 — EC2에서 `grep ADMIN_BOOTSTRAP_PASSWORD /opt/teslafleet/docker/.env`)로 생성.

---

## 5. 에러 코드 표

| Status | 의미 | 등장 endpoint |
|---|---|---|
| 200 | 정상 응답 | 전체 |
| 302 | OAuth redirect | `/auth/login`, `/auth/callback` |
| 400 | OAuth state CSRF 실패 · Tesla token 교환/refresh 실패 · onboard register 비정상 응답 | `/auth/callback`, `/auth/refresh/{id}`, `/onboard/register/{vin}` |
| 401 | onboard `_get_access_token` refresh 실패 | onboard 전체 |
| 404 | 차량/토큰/run/replay 없음 | `/vehicles/{id}`, `/telemetry/vehicles/{id}/*`, `/auth/refresh/{id}`, `/admin/sim/stop|runs/{id}`, `GET /admin/bronze-replay/{id}`, `POST /admin/bronze-replay/{id}/stop`, `DELETE /admin/bronze-replay/{id}`, `DELETE /admin/bronze-replay/ingested-vehicles/{id}` |
| 409 | onboard limit_reached · sim 활성 run 있음 · 이미 종료된/실행 중 replay · in-flight 삭제 job 중복 · duplicates 작업 중 | `/onboard/register/{vin}`, `DELETE /admin/sim/vehicles`, `POST /admin/bronze-replay/{id}/stop`(이미 종료), `DELETE /admin/bronze-replay/{id}`(pending/running), `DELETE /admin/bronze-replay/ingested-vehicles/{id}`(in-flight 삭제 중복), `POST /admin/duplicates/{scan,cleanup}`(scanning/cleaning 중) |
| 412 | confirm 토큰 불일치 | `PUT /settings/telemetry-config`, `POST /settings/repush-all`, `DELETE /admin/sim/vehicles`, `DELETE /admin/seed/vehicles/{id}`, `DELETE /admin/seed/events`, `POST /admin/seed/ingest-one`, `DELETE /admin/bronze-replay/ingested-vehicles/{id}`(`confirm=DELETE_INGESTED`), `POST /admin/duplicates/cleanup`(`confirm=DELETE_DUPLICATES`) |
| 422 | Pydantic 검증 실패 (body / query / path) | body 받는 POST/PUT 전체 + path UUID 잘못된 형식 + `last_days < 1` 등 query 제약 위반 |
| 429 | cooldown / 동시 실행 cap | `POST /settings/repush-all` (5분), `DELETE /admin/sim/vehicles` (5분), `POST /admin/sim/start` (cap 5), `DELETE /admin/seed/vehicles/{id}` (60s), `DELETE /admin/seed/events` (60s) |
| 502 | S3 list/get 외부 오류 (`POST /admin/seed/ingest-one`, `GET /admin/seed/monthly-overview`, `GET /admin/seed/list-month-files`) | seed 전체 |
| 500 | 설정 누락 · CA cert 디코드 실패 · 활성 신호 0 · id_token 디코드 실패 | `/auth/*`, `/onboard/*` |
| 502 | Tesla refresh 응답에 access_token 누락(`auth.py`/`onboard._get_access_token`) · seed S3 외부 오류 · lakehouse 토글 부분실패 복원·pipeline-status AWS 조회 실패 | auth/onboard/seed/lakehouse |
| 504 | 집계 `statement_timeout` 초과 | `GET /telemetry/.../events`(45s, detail=한국어 '기간을 좁히세요' 메시지) · `GET /telemetry/.../route`(45s, detail=`route_range_too_large`) · **차량 심화 분석 10종**(`charge-sessions`/`efficiency`/`driving-events`/`speed-histogram`/`places`/`battery-health`/`vampire-drain`/`activity-calendar`/`utilization`/`fleet-baseline`, 60s, detail=`range_too_large`, v1.7.7~v1.7.8) — detail 포맷이 endpoint별로 다름 |
| 503 | 월별 현황 집계 `statement_timeout`(45s, sqlstate 57014) 초과 — `ANALYZE` 후 재시도 | `GET /admin/seed/monthly-overview` |

---

## 6. Swagger UI / OpenAPI

FastAPI가 빌드 시 자동 생성하므로 별도 도구 불필요.

| URL | 내용 |
|---|---|
| `/docs` | Swagger UI (interactive — 직접 호출 가능) |
| `/redoc` | ReDoc (읽기 전용 — 인쇄 친화) |
| `/openapi.json` | OpenAPI 3.x JSON 사양 (코드 생성기 입력용) |

### 6.1 환경 변수

#### Backend / Frontend 공통

```
ENABLE_OPENAPI=1   # 노출 (default — dev/staging)
ENABLE_OPENAPI=0   # 비공개 (prod 권장 — admin/sim·settings에 인증 없어 직접 호출 위험)

REQUIRE_PROD_CONFIG=0  # 0: dev default(누락 시 hard-coded fallback) / 1: 누락 시 fail-fast
```

`backend/app/main.py`의 `_enable_openapi` 게이트. `ENABLE_OPENAPI=0`이면 세 URL이 모두 404를 반환합니다.

#### kafka_consumer (Kafka → RDS)

| 변수 | Default | 의미 |
|---|---|---|
| `KAFKA_BOOTSTRAP_SERVERS` | `10.0.0.211:9092` | Kafka broker (prod 모드에서는 명시 필수) |
| `KAFKA_GROUP_ID` | `teslafleet-backend-consumer` | consumer group |
| `KAFKA_MAX_RECORDS` | **`1000`** (2026-05-28 catch-up 가속) | batch 1회 최대 메시지 — 큰 값일수록 throughput ↑ but transaction 크기 ↑ |
| `VEHICLE_CACHE_MAX` | `10000` | VIN→vehicle_id in-process cache cap (FIFO eviction) |
| `CARRY_FORWARD_FORCE` | `0` | **1: forward-only ts 가드 우회**. S3 → Kafka replay 시 메시지 timestamp가 과거(예: 2025-02)라 prev_ts(현재)와 비교 시 carry-forward skip 되는 문제. replay 한정 ON. |

> **2026-05-28 batch 개선**: `process_v_batch_optimized` 도입 — batch 내에서 vehicle별 ts ASC 정렬 + progressive carry-forward + bulk INSERT(실패 시 single fallback). 처리 속도 80/s → 800-1,500/s (10-18x 향상). 정확성 100% 동일.

#### s3-archiver (Kafka → S3 raw archive + Bronze envelope dual-publish)

| 변수 | Default | 의미 |
|---|---|---|
| `S3_ARCHIVER_GROUP_ID` | `teslafleet-s3-archiver` | consumer group |
| `S3_RAW_BUCKET` | `teslafleet-dev-raw-telemetry-329599639037` | S3 archive 버킷 |
| `S3_PREFIX` | `topics` | S3 path prefix |
| `S3_BATCH_MAX_MESSAGES` | `1000` | flush 트리거 (메시지 수) |
| `S3_BATCH_MAX_BYTES` | `5242880` (5MB) | flush 트리거 (byte) |
| `S3_BATCH_MAX_SECONDS` | `60` | flush 트리거 (초) |
| `BRONZE_SINK_ENABLED` | **`1`** | 2026-05-x Phase A1 — `telemetry.raw.v1`에 envelope 동시 publish (Iceberg Bronze sink용) |
| `BRONZE_KAFKA_TOPIC` | `telemetry.raw.v1` | Bronze envelope publish 대상 topic (3 partition) |

> **Bronze envelope schema** (2026-06-01 **5 top-level field**): `event_id` (uuid4) / `source` (`tesla_fleet_v|tesla_fleet_alerts|...`) / `event_time` / `ingested_at` / `raw_payload` (원본 Tesla JSON string). 분석 필드(ident/lat/lon/speed_kph/organization_id/device_id/vehicle_id)는 `raw_payload`에 보존 → 하류 파싱(top-level 안정성 우선).

> **Iceberg Bronze 적재 경로**: s3-archiver → `telemetry.raw.v1` (Kafka) → **Kafka Connect Iceberg Sink** → Glue Catalog `teslafleet_bronze_dev.telemetry_raw` → S3 `warehouse/teslafleet_bronze_dev.db/telemetry_raw/data/` (Parquet, hidden partition `day(ingested_at)`). 별도 Connect EC2(t3.large) + 별도 SG.

### 6.2 운영에서 접근

운영 nginx는 `/api/*`/`/health`만 backend로 proxy하고, `/docs`·`/openapi.json`·`/redoc`은 frontend(Next.js 정적 export — nginx 정적 `out/` 서빙)로 가서 404를 반환합니다. backend의 Swagger를 접근하려면:

1. **로컬**: `docker compose up`(또는 `uvicorn`) 후 `http://localhost:8000/docs`
2. **운영 backend 직접**: SSM Session Manager로 EC2 접속 → `curl http://127.0.0.1:8000/openapi.json` (인증 우회 위험 — admin 사용 한정)
3. **nginx 라우트 추가**(권장 안 함, prod 노출 부담): `/docs`·`/openapi.json`도 backend로 proxy하도록 conf 수정

### 6.3 클라이언트 자동 생성

`/openapi.json`을 입력으로 클라이언트 코드 자동 생성 가능 — 예:

```bash
# TypeScript (openapi-typescript)
npx openapi-typescript http://localhost:8000/openapi.json -o frontend/src/lib/api/types.ts

# Python (datamodel-code-generator)
datamodel-codegen --input openapi.json --input-file-type openapi --output api_client.py
```

> 권장 운영: prod에서는 `ENABLE_OPENAPI=0`으로 닫고, 별도 staging 환경에서만 노출해 클라이언트 코드 생성에 사용.

---

## 알려진 이슈

| 이슈 | 영향 | 상태 |
|---|---|---|
| `GET /vehicles?data_source=seeded` ~90s → CloudFront 504 | `list_vehicles`가 대형 seeded(186만 events)에 `count+min+max` outerjoin+group_by full 집계 | **해소** (Alembic 0024) — vehicles에 `event_count`/`first_event_at`/`last_event_at` 비정규화 컬럼. list_vehicles 집계 제거(컬럼 직접). 응답 필드명(event_count/earliest_timestamp/latest_timestamp) 불변 — frontend 무변경 |
| 메인 화면(`GET /vehicles`)이 오래된 stat 노출 ("캐시 문제처럼 보임") | Alembic 0024 비정규화 후 `event_count`/`last_event_at`를 채우는 게 `resync_vehicle_stats`뿐 — startup + daily(1일). 라이브/시뮬 스트리밍 차량은 그 사이 최대 24h 멈춤 (CDN/Next 캐시 아님 — HTML `no-store`+CloudFront `Miss` 확인) | **해소** (`165f78e`) — write 시점 O(1) 증분: `kafka_consumer.handle_telemetry`(라이브+시뮬)·`seed._ingest_one_dump`(적재)가 INSERT와 같은 트랜잭션에서 `event_count+N`/`first·last_event_at` 갱신(`case` min/max, PG·SQLite portable). `resync_vehicle_stats`는 drift 보정 net로 격하(startup+daily). delete 후 일시 과대만 daily 보정(보고 증상 반대 방향). 라이브 검증: 60s sim 12 메시지 → 839→851 실시간(재시작·resync 없이), `last_event_at` 즉시 갱신 |
| Powershare 5신호 실데이터 부재 | S3 2025-11부터 출현하나 차량이 전부 `{"invalid":true}`로 전송(미측정) → parser invalid skip(정상) | **해소** — Alembic 0023으로 typed 컬럼 격상 + KEY_TO_COLUMN 매핑 + 대시보드 Powershare 그룹. 실데이터는 여전 invalid이나 시뮬레이터 idle 시나리오 active 값으로 end-to-end 검증 가능 |
| `telemetry_events` 중복 행 누적 | `(vehicle_id,timestamp)` 유니크 부재로 같은 메시지 재유입(Kafka at-least-once 재전달·Bronze Replay가 `tesla_V` 토픽 공유로 RDS 재적재·seed 재import)이 그대로 새 행 생성(553938 replay 이중적재 ~116만) | **해소** (Alembic 0040) — `uq_te_vehicle_ts_payload` 유니크 인덱스(`vehicle_id, timestamp, md5(coalesce(raw_data::text,''))`)로 exact 재전송본 INSERT 차단. consumer 3경로 + seed 2경로 `ON CONFLICT DO NOTHING` 멱등 적재. collision(같은 ts·다른 payload)은 보존. `GET/POST /admin/duplicates/{overview,scan,cleanup}`로 기존 누적분 조회·정리 |

---

## 변경 이력

> API 표면(endpoint·스키마·동작) 변경만 버전별 요약. 코드/인프라 상세는 `git tag -n99 v1.0.x` 또는 commit 메시지 참조.

### v1.9.0 (2026-07-03) — alembic head 0050 (스키마 무변경) · ⭐데이터 레이크 분석 신설(S3 Silver/Bronze Athena)

> **신규 admin 라우터 `admin/datalake`(5 엔드포인트) + FE `/admin/data-lake` 페이지.** 기존 RDS 실시간 화면 무변경.

- **무엇**: S3 Silver `telemetry_signals`(long 포맷 — **253 신호**·13.6M 이벤트·실차 7 VIN·2025-01~2025-11)와 Bronze 계약 검증 결과를 Athena로 조회하는 **정적 히스토리 분석**. RDS 화면이 구조화하지 않는 신호(셀 전압 Brick/NumBrick·모터 토크/전류·페달·충전기 전압·내비 ETA·LifetimeEnergyUsed 등)가 핵심 가치.
- **화면 4카드**(전부 Athena on-demand 버튼 실행): ①신호 탐색기(신호 ≤5 선택→신호당 미니 시계열) ②주행·에너지 히스토리 프리셋(Odometer·ACChargingEnergyIn·LifetimeEnergyUsed) ③배터리 셀 심화(min/max 전압·스프레드) ④계약 검증 상세(상태/실패코드 분포+실패 샘플). 페이지 컨트롤: VIN(RDS 이름 조인)·조회 기간(date 2개·기본=데이터 최신 30일)·SIM 포함 토글·"정적 스냅샷·파이프라인 OFF" 배지.
- **정책(사용자 확정)**: 파이프라인 OFF 유지(정적)·admin 전용·**쿼리 윈도우 스팬 ≤30일 서버 강제**(`422 datalake_range_too_large`, meta만 예외=컬럼 프루닝+6h 캐시).
- **과금/안전 가드**: workgroup `bytes_scanned_cutoff` 1GB(기존)·LRU/TTL 캐시(윈도우 1h·meta 6h — 정적이라 김)·Athena 동시 세마포어(2)·타임아웃 25s→504+서버측 쿼리 취소(폴링 예외 경로 포함)·vin/signal_key 정규식 화이트리스트(자유 SQL 없음)·`day(event_time)` 파티션 프루닝 강제.
- **정확성(적대검증 confirmed 3 반영)**: 버킷 산정 floor→**ceil**(floor면 버킷 수 최대 ~2×points로 max_rows 침묵 절단 — 신호 통째/시간 후반부 유실)+`truncated` cap-hit 플래그(응답·FE 경고, v1.7.6 events 교훈)·Athena 폴링 예외 시에도 best-effort stop(과금 지속 차단)·validation 윈도우에 `ingested_at IS NULL`(그 자체가 이상) 항상 포함·Athena timestamp ' UTC' 접미사 robust 파싱(FE).
- 신규 파일: `app/services/athena.py`(공용 쿼리 헬퍼·NextToken 페이지네이션, lakehouse.py 무변경)·`app/routers/datalake.py`·FE `app/admin/data-lake/` + `Datalake{MiniChart,SignalCard,ValidationCard,HistoryCard,CellsCard}` + 사이드바 '데이터 레이크 분석'(adminOnly)·`dl.*` i18n ko/en.
- 게이트 pytest **447**(datalake 10 신규)·ruff 신규 0·tsc·build. terraform 변경 0(기존 workgroup/IAM 재사용)·스키마 변경 0.

### v1.8.2 (2026-07-02) — alembic head 0050 (스키마 무변경) · 7단계 자율 감사(성능 to_thread·장애 견고화·회귀 하드닝)

> **엔드포인트 무변경. verify-otp에 `403 customer_not_assigned` 추가(login과 대칭·additive).** 나머지는 내부 성능/견고화.

- **MFA 경로 이벤트 루프 블로킹 제거(성능)** — `_read_mfa_secret`/`_set_mfa_secret`(KMS 봉투암복호화)·`_consume_backup_code`(백업코드 scrypt)·`mfa_enable`(백업코드 10× scrypt)를 `asyncio.to_thread`로 오프로드. 단일 uvicorn 워커에서 동기 KMS(~10-50ms)·scrypt(수십 ms)가 이벤트 루프를 직렬 블로킹하던 것 제거(auth.py·onboard.py의 기존 to_thread 패턴과 정합, 동작·반환 불변).
- **verify-otp 미분배 manager 차단(장애/정합)** — 챌린지 발급 후 verify-otp 전(≤5분)에 admin이 고객사 분배를 해제하면 미분배 manager로 세션이 발급되던 것 → `403 customer_not_assigned`(login과 대칭). ⚠️ 가드를 OTP/백업코드 **검증 앞**에 배치 — 검증 뒤면 백업코드가 소진(used=True 커밋)된 뒤 403이라 유한(10개)·1회용 코드가 세션 없이 소실(Phase4 자가발견 회귀→선제 수정).
- **외부 클라 타임아웃(장애 견고화)** — `encryption._kms_client`(로그인/MFA/토큰 경로)·`scheduled_tasks`의 secretsmanager 클라에 botocore `Config(connect=5s, read=10s, retries=2)` — 기본 60s hang 시 to_thread/poll 워커 장시간 점유 방지(alerts·lakehouse 클라와 동일).
- **백그라운드 UPDATE lock_timeout(장애)** — `_carry_forward_one_vehicle`(lifespan startup carry-forward)에 `SET LOCAL lock_timeout='3s'`+`statement_timeout=30s` — 라이브 consumer의 같은 vehicle 행 락과 경합 시 무한 대기→ingest stall 방지(초과는 caller per-vehicle try/except가 흡수·다음 주기 self-heal).
- **sim 전체삭제 락순서(장애)** — `_do_delete_all_sim_vehicles_background`가 vehicles 행을 canonical(`id::text`) 순 FOR UPDATE 선점 + `lock_timeout='3s'`(PG) — 다른 vehicles 대량 mutation의 데드락 invariant와 통일(consumer 교차 40P01 방지).
- **geocode error 절단** — Google `error_message`를 `ReverseGeocode.error`(String(256)) 저장 시 `[:256]` 절단 — 긴 메시지(URL 포함)의 PG StringDataRightTruncation→500 방지(예외 경로 `[:240]`와 일관).
- 게이트 pytest **437**(MFA 미분배 verify-otp TOTP·백업코드 회귀 테스트 +2)·ruff 신규 0. 적대 검증(Phase1 성능·Phase2-4 코드/장애·Phase4 회귀 각 워크플로): 성능 applySafe 2·코드/장애 confirmed 8→적용 6/skip 1(로그인 타이밍=상태코드 이미 노출)/propose 1(Silver 워터마크)·회귀 confirmed 1→수정. Tesla 연동 코드 변경 0(직전 CLEAN 유효).

### v1.8.1 (2026-07-02) — alembic head 0050 (스키마 무변경) · 보류 개선항목 6종 일괄(비용·Glue·운영 견고화·per-account cap)

> **엔드포인트 무변경. roads/geocode에 `rate_limited` 응답 status 추가(additive)·settings telemetry-config에 canonical 충돌 422 추가.**

- **roads/geocode per-account rate cap** — 유료 외부 API(Google Roads/Geocoding) 남용/폭주로 계정 하나가 비용을 무한정 발생시키는 것 방지. `POST /roads/snap`(30건/분·계정)·`GET /geocode/reverse`(120건/분·계정, **캐시 miss=실제 Google 호출에만 카운트** → 캐시 hit은 throttle 안 함). 초과 시 graceful: roads=`{status:"rate_limited", points:원경로}`·geocode=`{status:"rate_limited", address_full:null}`(DB 미기록→다음 호출 재시도). 프로세스-로컬 슬라이딩 윈도(`app/utils/rate_limit.py`·단일 워커 전제).
- **settings telemetry-config canonical 충돌 검출(422)** — alias(`ChargingState`)와 canonical(`ChargeState`)을 **둘 다 enabled**로 PUT하면 `_load_signal_fields`가 같은 canonical 키(`fields[canonical]`)를 display_order 마지막 것으로 silent 덮어써 한쪽 interval/minimum_delta가 유실되던 것 → 사전 422(`동일 canonical … 하나만 활성화`). enabled 신호만 검사(disabled alias 공존 무해).
- **Glue Bronze 검증 성능** — `bronze_contract_validation_job.py` 행단위 `F.udf`(레코드별 pickle)→`pandas_udf`(Arrow 컬럼 배치). 파리티 구조적 보존(event_time/ingested_at은 UDF 앞에서 `.cast("string")` → 타임스탬프 렌더링이 Spark cast에서 확정·UDF 종류 무관). ⚠️ 파이프라인 OFF라 라이브 검증은 다음 ON 시(result count 파리티·ExecSec↓).
- **배포 견고화** — deploy.sh가 `alembic upgrade head` 전 실패한 CONCURRENTLY 빌드 잔여물(INVALID 인덱스, `indisvalid=false AND indisready=false`)을 **`DROP INDEX CONCURRENTLY`**(autocommit·SHARE UPDATE EXCLUSIVE=라이브 consumer INSERT 비차단·lock_timeout 방어)로 정리(`scripts/drop_invalid_indexes.py`, 멱등·PG 전용·best-effort). 재시도가 'already exists'로 막히거나 플래너가 무시하던 것 방지.
- **VACUUM runbook** — 대량 삭제/backfill 후 온라인 `VACUUM (ANALYZE)` 절차(`VACUUM FULL` 금지·index-only scan 재활성) 문서화(BEEKEEPER §19).
- **비용** — kafka-connect EC2(t3.large, Lakehouse Bronze 적재)를 유휴(텔레메트리 정지·Glue OFF) 상태에서 **stop**(~$60/월 절감·메인 앱 RDS 분석 무관·재시작 가역). `aws_instance`는 전원상태 미관리라 terraform drift 없음.
- 게이트 pytest **435**(rate_limit·roads/geocode cap·settings collision 테스트 +10)·ruff 신규 0·Glue py_compile·deploy.sh bash -n. 적대 검증(6항목 find→verify): confirmed 1(deploy INVALID DROP의 lock 회귀)→CONCURRENTLY로 수정, 나머지 5 confirmed 0.

### v1.8.0 (2026-07-02) — alembic head 0050 (스키마 무변경) · 7단계 자율 감사 후속(성능 hot-path·운영 견고화·회귀 하드닝)

> **엔드포인트·스키마 무변경. 내부 성능/견고화 + 회귀 방지만.** 응답 형태·필드·동작 계약 불변.

- **차량 조회 hot-path JSONB 로드 제거(성능)** — `telemetry`/`analytics`의 존재·스코프 가드가 `session.get(Vehicle)`로 대용량 `latest_telemetry`(carry-forward JSONB) 전체 행을 로드하던 것을, 가드에 실제 필요한 `customer_id`(스코프)·`data_source`(캐시 TTL)·존재만 뽑는 좁은 select(`_guard_vehicle`)로 교체. 가드는 캐시 lookup **앞**(lesson #64)이라 캐시 HIT 경로에서도 매번 JSONB detoast가 발생해 캐시 이득을 상쇄하던 것을 제거(telemetry route/events/route/latest 4곳 + analytics 10개 엔드포인트, 기능·404 시맨틱 무변경).
- **위치 fallback·통계 재계산 statement_timeout 가드(운영 견고화)** — `GET /vehicles` lat/lng 미보유 차량의 `telemetry_events` DISTINCT ON fallback에 `statement_timeout=15초`(무경계 스캔이 db.t4g.small pool 점유 방지, 초과 시 빈 loc graceful)·`resync_vehicle_stats` 집계 UPDATE에 `120초`(lock_timeout과 함께 병리적 지연이 선점 락 무기한 점유 방지). PG 전용 분기.
- **커넥션 풀 컨테이너별 설정화** — `db.py` 하드코딩 20/20을 `DB_POOL_SIZE`/`DB_MAX_OVERFLOW` env로 주입 가능하게(기본 20/20 보존). backend·consumer가 같은 엔진 코드를 공유해 각각 40커넥션을 열 수 있던 것을, consumer는 `CONSUMER_DB_POOL_SIZE`/`CONSUMER_DB_MAX_OVERFLOW=5`(docker-compose 기본)로 축소해 RDS max_connections 여유 확보.
- **회귀 하드닝(Phase4 적대 재검토 confirmed 2·둘 다 MED)**: ① 알림 이메일 구독 중복 가드가 **PendingConfirmation(미확인)까지 skip**해, 확인 토큰(~3일) 만료 후 미확인 행(AWS 최대 30일 잔존)에 재확인 메일도 못 보내고 ARN 없어 삭제도 못 하는 데드엔드가 되던 것 → **확인된 구독만 skip**, 미확인은 재구독(새 확인 메일 재발송=유일 인앱 복구 경로). ② FE 상세 페이지 고객사 필터 저장 effect가 `authLoading` 가드 누락으로 auth 미확정 창에서 매니저 `customer_id`를 공유 localStorage에 오염 기록하던 fail-open → 자매 페이지와 동일 `authLoading||isManager` 가드(lesson #69).
- **FE 소소 견고화**: MfaSetup QR 등록을 마운트 1회로(로케일 변경 시 `mfaSetup()` 재호출→provisional secret 흔들림 방지, 에러는 render 시 번역)·로그인 백업코드 소진 임박(≤3) 경고 화면(재발급 안내).
- **인프라(코드만·apply 불필요)**: RDS `lifecycle.ignore_changes`에 `allocated_storage` 추가 — 스토리지 오토스케일(max_allocated=200)이 AllocatedStorage를 20 위로 키운 뒤 다음 apply가 20으로 축소 시도→RDS 거부→이후 모든 인프라 변경 차단되던 잠재 drift 방지(engine_version과 동일 AWS-관리 drift 클래스).
- 게이트 pytest **425**(alerts 구독 confirmed/pending 회귀 테스트 +2)·ruff 신규 0·tsc·build. Tesla 연동 코드 변경 0(직전 CLEAN 유효).

### v1.7.9 (2026-06-30) — alembic head 0050 (테이블 스키마 무변경·charge/places 인덱스 0049/0050) · 7단계 감사 + 분석 UI 보강 + 충전 습관 점수

> **엔드포인트 무변경. 거리 계산 누출 면역 확장 + 충전 판정 강화 + 안전 하드닝(7단계 자율 감사) + 분석 UI 보강(driving-events 응답에 `speed_matrix`·charge-sessions 응답에 `habits` additive·배터리 에너지 추세 FE 렌더).**

- **driving-events·activity-calendar 거리도 daily-min-delta로** — efficiency가 쓰던 누출-면역 일별-최소-진행을 driving-events 점수 분모(`dist_km`)와 activity-calendar에 확장(신규 `_window_dist_km`). 윈도 단일 max(odo)-min(odo)이 명시 from/to 내부날 종료 시 미래 odometer 누출로 부풀어 점수 과대/히트맵 왜곡되던 것 정정. 단조 정상 데이터·last_days 윈도는 값 불변(telescoping=max-min). activity-calendar 마지막날 폴백에 물리 1500km 캡.
- **charge-sessions 충전전력 가드 추가** — `charge_state='Charging' AND speed≤1` → **`+ charging_power_kw>0`**. 충전 종료 후 정차 stuck-'Charging'(전력=0) 행이 세션에 병합돼 duration/end_soc 오염되던 잔존 sticky 제거(라이브 정밀 99%+).
- 견고화(코드만·무계약변경): s3_archiver boto3 명시 타임아웃(다른 AWS 클라와 일관)·FE 카드 useMemo 안정화·ChargeCard 역지오코딩 좌표키·latest 스냅샷 fetch abort·충전권장 좁은윈도 게이트·_window_dist_km 자기 statement_timeout 가드. FE 심화분석 4카드(자주가는장소·가동률·배터리건강도·충전권장+대기방전 병합) on-demand 버튼화·Powershare 무데이터 섹션 숨김.
- **속도대별 위험 매트릭스(driving-events 응답에 `speed_matrix` 추가 — additive)** — 운전 점수 카드에 급조작을 속도밴드(0/30/60/90/120+ km/h)×유형(급가속/급제동/급선회)으로 집계한 히트맵 추가(전체 클러스터 기준·표시캡 무관). 저속 주차 횡가속 노이즈와 고속 코너링을 분리해 '어느 속도대에서 위험했는지' 노출.
- **배터리 에너지 용량 추세(battery-health FE 렌더 — 응답 무변경)** — 기존 `summary.energy`·`points[].full_energy_kwh`(이미 응답 포함)를 정격거리(좌축 km)와 함께 우축(kWh)에 겹쳐 그리고 에너지 최근/기준/열화% 지표 추가.
- **충전 습관/스트레스 점수(charge-sessions 응답에 `habits` 추가 — additive)** — 충전 세션 집계로 배터리 친화 점수(0~100) 산출(추가 쿼리 0·같은 세션 목록 재사용). DC 급속 비율·종료 SoC≥90% 비율·시작 SoC≤10% 비율을 가중평균(SoC 결측 재정규화·세션<3이면 null·신뢰 SoC 세션<3이면 SoC 지표 제외). FE `ChargeHabitsCard`(점수·등급·3비율·평균 시작/종료 SoC·조언·SoC 표본수 m/n·truncated 경고). 적대 감사 confirmed 4 반영(MEDIUM 2·LOW 2). **DC 패널티 완화**(사용자 피드백 2026-06-30, Yuna 100% DC): DC 서브점수 `100−40·비율`(100% DC→60 '보통', 0/'주의' 아님 — 급속은 필요성 많음)·신뢰 SoC 세션<3이면 'SoC 표본 부족' 캐비엇 노출.
- **AC/DC 판정 정확화(기존 charge-sessions `charge_type`에도 적용)** — DC 보조 임계 `_CHARGE_DC_PEAK_KW` **20→50kW**(CCS/슈퍼차저 하한)로 상향 + **의미있는 `fast_charger_type` 신호가 있을 때만** 신뢰(피크 보조 판정 봉쇄). 3상 AC(≤22kW)가 DC로 오분류되어 습관 점수 DC 비율을 부풀리던 것 정정. 3회차 종합감사(LOW): `Unknown`뿐 아니라 **`SNA`/`Other`/`Invalid`(식별 불가·미신뢰)도 신뢰 신호에서 제외**(`_UNTRUSTED_CHARGER_TYPES`, `type` 접미 잔존형까지 `removeprefix` 정규화) — carry-forward stale 값이 진짜 DC 세션 폴백을 무력화하던 경로 차단. places/driving-events `truncated` 판정을 `CAP+1`/`>`로 정밀화(charge-sessions와 정합·정확히 CAP일 때 오탐 제거).
- **⚡alembic 0050 — places 인덱스 신설(`ix_te_places`)** — 사용자 보고('자주 가는 장소' 1개월 504) EXPLAIN ANALYZE 실측: places가 lat/lng를 커버하는 인덱스가 없어 **Parallel Seq Scan**으로 전체 테이블(MDP 30일 Rows Removed 3.89M·shared read 643K buffers ~5GB·I/O 38s)→504. 정차 샘플만 담고 lat/lng를 INCLUDE한 커버링 부분 인덱스 `(vehicle_id,timestamp) INCLUDE(latitude,longitude) WHERE speed_kph≤3.0 AND lat/lng NOT NULL`로 **Index Only Scan(Heap Fetches 0)** 전환 → MDP 43.3s→5.7s. places PG SQL의 speed 임계를 바인드→리터럴 인라인(부분 인덱스 매칭). CREATE/DROP CONCURRENTLY·PG 전용.
- **⚡alembic 0049 — charge-sessions 인덱스 정밀화(`ix_te_charging` → `ix_te_charging_active`)** — 사용자 보고('1개월인데 기간 너무 김' 504) EXPLAIN ANALYZE 실측: 0047의 `ix_te_charging` predicate `charge_state='Charging' OR charging_power_kw>0.1`가 carry-forward sticky 전력행까지 담아 'Charging' 15행뿐인 비활성 차량도 (vid,ts) 범위 ~115K행을 인덱스 스캔→heap 필터(Rows Removed 115,033·I/O ~9.8s)→cold/경합 시 60s 504. 쿼리 필터를 그대로 담은 부분 인덱스(`WHERE charge_state='Charging' AND charging_power_kw>0 AND (speed_kph IS NULL OR speed_kph<=1)`)로 교체 → 매칭 행만 index range scan(sub-second). 넓은 옛 인덱스는 charge-sessions 외 소비처 없어 DROP. CREATE/DROP CONCURRENTLY·PG 전용.
- 게이트 pytest **420**·ruff·tsc·build. 7단계 감사 Step1-4 confirmed 10/적용 9·Step4 회귀 0.

### v1.7.8 (2026-06-29) — alembic head 0048 (스키마 무변경) · 분석 10종(가동률·커버리지) + 충전 정확성 정정

> **가동률·커버리지 endpoint 신설 + 라이브 교차확인 기반 정확성 정정(sticky 'Charging' 오분류).** 엔드포인트 **97→98개**.

- **`GET /api/v1/telemetry/vehicles/{vehicle_id}/utilization` 신설**(#util·`require_account`·`GET`) — 주행/충전/주차 시간 점유(가동률) + 수집 공백(커버리지 헬스). 연속 샘플 간격을 **속도 우선**으로 상태 귀속 + **쿼리 시점 last-value 채움**(적재 carry 여부 무관). PG는 window(`first_value` last-non-null + `LAG`) 단일 집계(ix_te_battery_vampire 커버링 index-only). 상세 [3.5.1](#351-차량-심화-분석-apiv1telemetry--v177).
- **⭐충전 판정에 정지 가드 추가** — `charge-sessions` WHERE가 `charge_state='Charging'` → **`charge_state='Charging'` AND `speed_kph≤1`(또는 NULL)**. 라이브 교차확인(2026-06-29): carry-forward가 충전 종료 전이 누락 시 'Charging'을 주행 내내 고착(Yuna 'Charging' 34,642행 중 80%가 speed>1) → 충전 세션에 주행 병합/duration 과대를 유발하던 데이터 오류. 정지 가드로 실충전만(라이브 정밀 99%+). (가동률도 동일 속도 우선 분류로 27,884건 오분류 해소.)
- **FE 분석 카드 추가**(frontend-only, API 무변경): 최근 상태 요약(`/vehicles/{id}/latest` 재사용)·충전 권장(스냅샷+대기방전+전비, 주차/주행 시나리오 분리)·가동률·커버리지(`/utilization`).
- alembic head·스키마 무변경(0048 유지) — `/utilization`은 기존 `ix_te_battery_vampire` 커버링 인덱스 재사용.

### v1.7.7 (2026-06-26) — alembic head **0048** (분석 가속 인덱스 0047/0048)

> **차량 데이터 심화 분석 9종 신설 + 충전 판정 정정 + Bronze Replay 토픽 누락 가드.**

- **차량 심화 분석 9 endpoint 신설**(`backend/app/routers/analytics.py`, prefix `/telemetry`, 전부 `require_account`·`GET`): `charge-sessions`(#1,#8)·`efficiency`(#2)·`driving-events`(#7)·`speed-histogram`(#10)·`places`(#9)·`battery-health`(#11)·`vampire-drain`(#12)·`activity-calendar`(#13) + `fleet-baseline`(전 차량 비교 기준선, `customer_scope` 미적용 의도적). 파라미터 `from`/`to`/`last_days`, 결과 캐시 TTL live 300s/정적 1800s, PG `statement_timeout=60s` 초과 시 `504 range_too_large`. 상세 [3.5.1](#351-차량-심화-분석-apiv1telemetry--v177).
- **⭐충전 판정 = `charge_state='Charging'`만**(charging_power_kw 아님 — 라이브 실측 전력>1 샘플의 84~88%가 Disconnected/Idle이라 가짜 세션 유발). `charge-sessions` 세션에 **`soc_unreliable`**(SoC 비단조 진동 시 true) 필드 추가.
- **alembic 0047** — 심화 분석 가속 인덱스 3종(전부 PG 전용·`CREATE INDEX CONCURRENTLY`): `ix_te_harsh_accel`(부분, `WHERE abs(longitudinal_acceleration)>=3 OR abs(lateral_acceleration)>=3`)·`ix_te_charging`(부분, `WHERE charge_state='Charging' OR charging_power_kw>0.1`)·`ix_te_analytics_metrics`(커버링, `(vehicle_id,timestamp) INCLUDE(speed_kph,odometer_km,lifetime_energy_used_kwh,outside_temp_c)`).
- **alembic 0048** — `ix_te_battery_vampire`(커버링, `(vehicle_id,timestamp) INCLUDE(battery_level,rated_range_km,energy_remaining_kwh,speed_kph,charging_power_kw,charge_state)`) — battery-health/vampire-drain cold 스캔 가속.
- **Bronze Replay 토픽 누락 가드**: `GET /admin/bronze-replay/preview` 응답에 **`omitted_topics[]`**(`{topic, object_count}` — 단일 저장 토픽 prefix가 같은 기간 형제 저장 토픽 누락 시 경고) + `POST /start` body **`allow_partial`**(기본 false) — 누락 시 `409` 차단, true로 우회.
- 엔드포인트 총 **82→97개**.

### v1.7.6 (2026-06-24) — 스키마 무변경 (alembic head 0046 유지)

> **어드민 계정 승격/강등 — 가입(manager) → admin 승격으로 어드민 추가 경로 신설.**

- **`POST /admin/accounts/{id}/role`**(`require_admin_session`): manager↔admin 역할 변경. 기존엔 부트스트랩(admin 0명·`ADMIN_FORCE_RESET`) 외 어드민 추가 경로가 전무 → DB 직접 수정만 가능했던 갭 해소.
- 승격(manager→admin): `customer_id` 해제 + 세션 revoke + 감사 `admin_promote`. 강등(admin→manager): 세션 revoke + 감사 `admin_demote`(신규 AuditEvent).
- **마지막 admin 강등 차단**(`400 last_admin`): admin 행 `FOR UPDATE`로 동시 강등 레이스까지 직렬화 — 전원 잠금 방지.
- FE `/admin/accounts`: 매니저 행 '어드민 승격' / 어드민 행 '매니저 강등'(마지막 1명 비활성). 적대 검증 9발견 real 0.

### v1.7.5 (2026-06-24) — alembic head **0046**

> **계정 로그인 OTP 앱(TOTP) 다단계 인증 — 전 계정(admin+manager) 2단계 로그인.**

- **alembic 0046**: `accounts`에 `mfa_enabled`(bool)·`mfa_secret_ct/nonce/dek`(TOTP secret KMS 봉투암호화)·`mfa_backup_codes`(1회용 코드 scrypt 해시 JSON)·`mfa_enrolled_at`·`mfa_last_used_step`(replay 차단) 추가. 전부 nullable/default — 기존 계정 무중단(미등록).
- **로그인 2단계**: MFA 등록 계정은 `/login`이 세션 대신 `{mfa_required, mfa_token}`(5분 HMAC 챌린지) 반환 → **`POST /login/verify-otp`**(OTP 6자리 또는 백업코드)로 세션 발급. OTP 오답은 비번 단계와 같은 잠금 카운터.
- **등록**: **`GET /mfa/setup`**(provisional secret + otpauth URI/QR) → **`POST /mfa/enable`**(첫 코드 확인 → enabled + 백업코드 10개 **1회 반환**). **`POST /mfa/disable`**(본인, 비번 재확인).
- **의무화(점진)**: `ACCOUNT_MFA_ENFORCE=0`(기본)=등록 계정만 OTP 요구, `1`=전 계정 등록 의무화(미등록 데이터 라우트 `403 mfa_setup_required` — SPA 등록 게이트). `me`/account payload에 `mfa_enabled`·`mfa_required` 추가.
- **복구**: **`POST /admin/accounts/{id}/reset-mfa`**(manager 한정·`require_admin_session`) / admin 본인은 비상 env `ADMIN_MFA_RESET=1` 1회 배포.
- **replay 차단(RFC 6238 §5.2)**: 사용한 TOTP step을 `mfa_last_used_step`에 소비 기록 — 같은 코드 재제출 `401 mfa_code_reused`.
- **안전 롤아웃**: TOTP는 stdlib 직접 구현(신규 백엔드 의존성 0)·FE QR은 `qrcode.react`. 기본 OFF 배포 → admin 자가 등록(+백업코드) → enforce ON.

### v1.7.4 (2026-06-18) — alembic head **0045**

> **보안 감사로그 + 활성 세션에 접속자 IP + 대략 위치(국가/도시) 표기.**

- **alembic 0044**: `account_audit_log`에 `ip_address`(String45·원문 IP)·`country`·`city`(String64) 3컬럼 추가(전부 nullable). 기존 `ip_hash`(PII 완화 해시)는 세션 비교용 유지.
- **alembic 0045**: `account_sessions`에 동일 3컬럼 추가 — 활성 세션 목록 표기용(로그인 시점 IP/위치, 토큰 회전 시 같은 행 유지).
- **`GET /admin/accounts/audit`** 응답 entries에 `ip_address`·`country`·`city` 추가(로그인·비번변경·세션 revoke·분배/리셋/삭제 등 request 있는 이벤트, bootstrap 등 시스템 이벤트는 null). **`GET /auth/account/sessions`** 응답에도 동일 3필드 추가.
- **위치 출처 = CloudFront viewer 헤더**: origin request policy를 `AllViewerAndCloudFrontHeaders`로 변경하면 edge가 `CloudFront-Viewer-Country-Name`/`-City`를 주입 → 백엔드가 읽어 저장(GeoIP DB·외부 API 불요, 앱이 전부 CloudFront 뒤라 실트래픽 100% 커버). 정책 미적용 시 IP만 채워지고 위치는 null. IP 출처 = **CloudFront-Viewer-Address**(IP:port, edge가 set이라 위조 불가) 1순위, 헤더 부재 시 X-Forwarded-For 최좌측→peer 폴백(XFF 최좌측은 클라 위조 가능해 위치와 동일 CloudFront-Viewer-* 출처로 통일).
- FE: AuditLogCard 'IP·위치' 컬럼(상세 컬럼은 기본 가림+hover 표시) + SessionsDialog 세션 행에 IP·위치 표시(admin/본인).
- **IP/위치 값 처리 견고화(자율 감사 후속, 동작 정밀화 — 스키마·엔드포인트 불변)**: ① `CloudFront-Viewer-Address`의 **괄호 없는 IPv6**(알려진 CloudFront 동작)를 `ipaddress` 검증으로 처리 — 단순 `rsplit(":")`가 마지막 hextet을 포트로 오인해 IPv6를 손상시키던 것을 방지(전체가 유효 IP면 절단 안 함). ② `CloudFront-Viewer-City`/`-Country-Name`의 **비-ASCII는 RFC 3986 percent-encoding**으로 전달되므로 `unquote`(UTF-8) 디코드 후 저장(São Paulo·한글 등이 `%XX%XX` 원문으로 깨져 저장·표시되던 것 해소). ③ 디코드 결과의 **NUL(`%00`)·제어문자 제거**(탭→공백) — PG `varchar`가 NUL을 거부해 헤더 위조 시 세션/감사 INSERT가 실패하던 경로 차단(graceful).
- **운영 견고화(자율 감사 — 내부 타임아웃·락 안전망, 스키마·엔드포인트 불변)**: ① `GET /admin/seed/monthly-overview` DB 집계에 `statement_timeout=45s` + 초과 시 **503**(풀스캔이 cache lock 장기 점유 방지). ② `GET /admin/kafka-lag`에 aiokafka `request_timeout_ms=5000` + `asyncio.wait_for(12s)` — broker 다운 시 cache lock hang 방지(stale/502 graceful). ③ consumer 배치 트랜잭션에 `SET LOCAL lock_timeout=3s`(PG) — `missing_vins` 비정렬 UPDATE의 데드락 무한대기를 fast-fail→seek-back→멱등 재시도로 전환(데드락 invariant 안전망). ④ `geocode/reverse`의 `address_short`를 레벨 조합 경로에서도 `[:128]` 절단(`String(128)` 초과 500 방지).

### v1.7.3 (2026-06-17) — alembic head **0043** (변동 없음)

> **차량 identity 보강(model/display_name "Unknown" 해소) + 자율 감사 후속.**

- **신규 엔드포인트 1개** `POST /api/v1/vehicles/admin/backfill-identity`(admin/require_admin_account): 기존 차량 identity 1회 보강 — model(VIN 4번째 자리 디코드 5YJ3…→Model 3)·display_name(telemetry_events.raw_data 최신 `VehicleName` 정제). 배포 consumer(process_v_batch_optimized)와 동일 정책(model='Unknown'·display_name placeholder만 갱신, 수동·실명 보존). 멱등. UPDATE는 str(id) 정렬(데드락 invariant)·`SET LOCAL lock_timeout='3s'`(라이브 consumer 행 락 경합 시 fast-fail skip)·SAVEPOINT 격리. name 조회는 placeholder 차량만(`statement_timeout=30s`). **응답** `{updated,total,changes[{vin(마스킹),model[전,후],display_name[전,후]}],name_unresolved,name_timed_out,name_failed,lock_skipped}`(뒤 4개 0이 정상 — 미해결/timeout/쿼리결함/락경합 skip 가시화).
- **consumer 자동 보강**(API 표면 무변경): kafka_consumer auto-register가 실VIN을 VIN 디코드 model·`"{model} (vin6)"` placeholder로 등록, process_v_batch_optimized가 VehicleName 신호로 placeholder display_name 보강(기존 단일 vehicle UPDATE에 CASE 합류 — 별도 UPDATE 없음=데드락 invariant 유지).
- 엔드포인트 총 **81→82개**. 본 작업은 2026-06-17(v1.7.2 릴리스 이후)이라 별도 버전으로 귀속.

### v1.7.2 (2026-06-16) — alembic head **0043** (변동 없음)

> **장애 이메일 알림 — CloudWatch RDS 저장공간 알람 → SNS email + Admin UI.**

- **신규 엔드포인트 4개** `/api/v1/admin/alerts/*`(admin): `GET /status`(알림 ON/OFF·알람 상태·수신 이메일 구독 목록), `POST /toggle?enabled=`(CloudWatch 알람 `actions_enabled` 토글), `POST /email`(SNS subscribe — 확인 메일), `DELETE /email`(확인된 구독 unsubscribe).
- 대상: **RDS FreeStorageSpace < 2GiB**(DiskFull 사고 재발 방지). 알람 **기본 OFF**. SNS 토픽 `teslafleet-dev-ops-alerts`·알람·IAM은 terraform(`infra/envs/dev/alerts.tf`) 생성, **수신 메일 구독은 UI(boto3)가 전담**.
- DB 스키마/마이그 무변경(인프라 — SNS 토픽 1·CloudWatch 알람 1 신규). consumer stall·24h 무적재 알람은 추후 확장(백엔드 커스텀 메트릭 publisher 필요).

### v1.7.1 (2026-06-15) — alembic head **0043**

> **계정 보안 강화(P0+P1) — 잠금·강제 비번변경·세션관리·감사로그.**

- **로그인 잠금**: 계정 단위 실패 추적(`failed_login_count`) → `login_max_failures`(8) 초과 시 지수 백오프 잠금(`429 account_locked`, base 60s~상한 3600s). 성공 시 리셋.
- **첫 로그인 강제 비번변경**: 가입/리셋/부트스트랩 계정은 `must_change_password=true` — 데이터/admin 라우트 `403 password_change_required`, `/auth/account/password`로 변경해야 해제. me/account payload에 `must_change_password` 포함.
- **비번 정책**: 변경 시 **≥10자 + HIBP 유출비번 거부(k-anonymity, fail-open) + 재사용 금지 + 디폴트(`modapl#123`) 금지**(`422 weak_password`·`pwned_password`·`password_reuse`). **must_change 계정은 현재 비번 불요**(이미 디폴트/리셋 비번으로 로그인 인증), 일반 계정은 현재 비번 필수·검증.
- **세션 관리**: `GET/DELETE /auth/account/sessions` + `revoke-others`(내 활성 세션·원격 로그아웃). 세션에 IP해시·UA·last_seen 기록 + **유휴 만료**(7일 무활동) + __Host- 쿠키 prefix.
- **영속 감사로그**(`account_audit_log`, 0042): 로그인·비번·분배·삭제·승격·세션 등 보안 이벤트 DB 기록. `GET /admin/accounts/audit`.
- **X-Admin-Key 스코프 분리**: 파괴적 계정작업(분배/리셋/삭제)은 `require_admin_session`(admin 세션 전용, 키는 `403`, `admin_key_block_dangerous=1`). 키 사용 로깅.
- **Admin 복구**: `ADMIN_FORCE_RESET=0→1` 전이에만 1회 발화하는 **one-shot edge-trigger**(`account_audit_log` sentinel + `force_reset_rearm` 이벤트) — `ADMIN_EMAIL` 계정을 `ADMIN_BOOTSTRAP_PASSWORD`로 강제 리셋(분실 복구). 자동 재시작(RDS rotation watcher·OOM·크래시)으로 인한 재발화로 admin이 변경한 비번을 되돌리는 회귀를 차단. `deploy.sh`·`fix-env.sh`가 `ADMIN_FORCE_RESET`을 **항상 0으로 고정**(보존 안 함) — 복구가 필요하면 운영자가 수동 1 설정 후 1회 부팅. 부트스트랩 비번은 must_change로 **1회용화**(P0).
- **alembic 0043**: `account_audit_log (event, created_at)` 복합 인덱스 `ix_account_audit_log_event_created` 추가 — `GET /admin/accounts/audit`의 event 필터 + created_at DESC 정렬을 backward index scan으로 커버(perf audit R1). **API 표면 무변경**.

### v1.7.0 (2026-06-12) — alembic head **0041**

> **계정/권한 관리(API 표면 대규모 변경) — nginx Basic auth 제거.**

- **계정 인증 5엔드포인트 신설**(`/auth/account/{signup,login,logout,me,password}`): Manager 가입은 **email만**(비번 디폴트 `modapl#123`), Admin이 고객사 분배 전 로그인 차단(`403 customer_not_assigned`). 세션은 `tf_account` HttpOnly 쿠키(30일, **v1.7.1에서 `__Host-tf_account`로 변경**) + DB 서버측(`account_sessions`, sha256) — 리셋/분배 변경 시 즉시 revoke.
- **계정 설정 4엔드포인트 신설**(`/admin/accounts*`, admin 전용): 목록(+email 검색·미분배 우선)/고객사 분배·해제/비번 리셋(디폴트+미분배 강등+세션 revoke)/삭제. admin 계정은 대상 아님(400).
- **전 데이터 라우터 인증 의무화**: vehicles/telemetry/geocode/roads/customers에 `require_account` — Basic auth 제거로 nginx 게이트가 사라지므로 무세션 `401`. admin 라우터는 `require_admin_account`(admin 세션 또는 X-Admin-Key, manager는 `403`). `ACCOUNT_AUTH_ENFORCE=0`(기본)이면 legacy 무인증(테스트/로컬 dev), deploy.sh가 1 설정.
- **Manager 고객사 스코핑**: vehicles 목록(쿼리 파라미터 override)·stats(필터)·상세/latest/refill + telemetry events/count/route/alerts/latest + customers 목록/상세 — 타 고객사 자원은 **404**(존재 누설 차단), 기존 404 가드(캐시 앞) 위치에서 강제.
- **SPA**: `NEXT_PUBLIC_ADMIN_KEY` 번들 주입 제거(공개 번들 키 유출 차단), `/login` 페이지 + AuthGate + role 메뉴 게이팅(Manager=메인현황·차량정보만) + 계정 설정 페이지 + 사이드바 계정 영역(비번 변경/로그아웃).
- **Admin 부트스트랩**: lifespan이 admin 0명일 때 `ADMIN_EMAIL`(기본 dev@modapl.com)+`ADMIN_BOOTSTRAP_PASSWORD`(deploy.sh 1회 생성·.env 보존)로 생성.

### v1.6.9 (2026-06-12) — alembic head **0040**

> **중복 데이터 차단 + 정리 기능(API 표면 변경).**

- **중복 조회·정리 3엔드포인트 신설**(`require_admin`): `GET /admin/duplicates/overview`(중복 그룹 수·exact 초과 행 수 요약), `POST /admin/duplicates/scan`(timestamp 윈도우 청크로 중복 그룹 스캔), `POST /admin/duplicates/cleanup`(exact 중복 제거 — keeper=typed non-null 최다·동률 id 최소, 디스크 스필 차단 윈도우 청크). 메인현황과 분리해 `Seed 관리` 하위 **데이터 현황** 탭에 노출.
- **`telemetry_events` 유니크 인덱스(Alembic 0040)**: `uq_te_vehicle_ts_payload`(`vehicle_id, timestamp, md5(coalesce(raw_data::text,''))`)로 exact 재전송 중복 INSERT를 **DB 단계에서 차단**. CONCURRENTLY 생성(락 회피) + 생성 전 기존 중복 윈도우 청크 제거. collision(같은 ts·다른 payload)은 보존.
- **멱등 적재(`ON CONFLICT DO NOTHING`)**: `kafka_consumer` 3 INSERT 경로(라이브 배치·단건 fallback) + `seed` 2경로(벌크·단건 fallback)에 추가. 충돌 skip은 정상 처리(실패 카운트 미반영, `event_count` 증분도 실제 INSERT rowcount로 게이팅). 응답 스키마·필드명 불변 — frontend 영향 없음.

### v1.6.3 (2026-06-02) — alembic head **0038** (변동 없음)

> **audit fix(API 표면 변경).**

- **일괄 sim 삭제 async**: `DELETE /admin/sim/vehicles`가 삭제 대상 events/alerts 0건이면 동기 `200 OK`(`status:"ok"`), 비-0건이면 `202 Accepted`(`status:"started"` + `job_id`/`expected_events`/`expected_alerts`/`message`) 반환 후 background task로 실 DELETE — 대용량 CASCADE 동기 삭제의 CloudFront 504 + PG long-tx/lock 잔존 차단(seed/bronze_replay와 동일 패턴). 진행은 `GET /admin/seed/delete-jobs/{job_id}` polling(`bulk-sim:` prefix audit). 동시/더블클릭 시작 시 `409`(`_resolve_or_reject_in_flight`, stale 초과 자가복구).
- **`minimum_delta` numeric-only 검증**: `SignalConfigIn`에 `_minimum_delta_numeric_only` model_validator 추가 — `minimum_delta` set 시 alias 정규화 후 `NUMERIC_SIGNALS`(35개) 외 신호(enum/bool)면 `422`(`minimum_delta는 숫자 신호에만 허용됩니다 (Tesla 공식 numeric-only): <signal_name>`). `PUT /settings/telemetry-config`가 Tesla push 거부를 사전 차단.

### v1.6.2 (2026-06-02) — alembic head **0038**

> **인증/보안 정합 audit fix(API 표면 변경).**

- **admin 앱-레벨 인증**: admin 영역(`settings`/`admin/sim`/`admin/seed`/`admin/bronze-replay`/`admin/kafka-lag`)에 `require_admin` dependency 부착 — `X-Admin-Key` 헤더를 `ADMIN_API_KEY`와 상수시간 hmac 비교. `ADMIN_AUTH_ENFORCE=1`(prod cutover 완료)이면 불일치/누락 시 `401`. SPA는 `NEXT_PUBLIC_ADMIN_KEY`로 자동 전송. `/customers/*`·`/geocode`는 미부착(무인증).
- **onboard 세션 쿠키 IDOR fix**: `onboard.*`(`/products`·`/vehicles`·`/register/{vin}`)가 owner_id를 쿼리 파라미터가 아닌 HMAC 서명 세션 쿠키(`tf_onboard_owner`)에서만 도출(`get_authenticated_owner`). 쿼리 owner_id 불신, 쿠키 없음/변조 시 `401 reauth_required`. OAuth callback이 해당 쿠키를 `Set-Cookie`(domain=`.tesla.modapl.dev`, 30일)로 발급.
- **OAuth scope 축소**: `vehicle_charging_cmds` 제거(데이터 수집 전용 — 최소권한). `vehicle_location`은 GPS/속도/Shift 신호에 필수로 유지.
- **ingested delete in-flight 409**: `DELETE /admin/bronze-replay/ingested-vehicles/{id}`에 `_resolve_or_reject_in_flight('ingested:')` 가드 추가 — 동시/더블클릭 삭제 시 `409`(stale 초과 자가복구).

### v1.5.0 (2026-05-21) — alembic head **0030**

> **고객사(Customer) 등록 기능 + 100회 검토 ×2 종합 fix(CR 6 / H 11).**

**2차 검토(4 agent 병렬) — 추가 fix**:
- **Tesla CR1**: `_extract_value`에 `tireLocationValue` 분기 추가 + `parse_message_dict`가 `TpmsHardWarnings`를 `tpms_hard_warning_{fl,fr,rl,rr}` 4컬럼에 분해(실차량 TPMS 경고 영구 NULL 차단)
- **BE CR1**: `POST /customers/{id}/vehicles` 사전 vehicle_ids 존재 검증 + 단일 SQL bulk UPDATE(missing은 400 반환). 누락 silent skip 대신 명시적 실패
- **BE H3**: `_ingest_one_dump`의 SeedImport IntegrityError 시 409 reject(이전: silent proceed → 중복 적재)
- **BE H2**: `CustomerCreate.name` Pydantic `Field(min_length=1, max_length=64)` + `CustomerVehiclesUpdate.vehicle_ids` `Field(min_length=1, max_length=500)` DoS 가드
- **Infra CR1**: `deploy.sh`가 매 배포 `s3://.../deploy/versions/teslafleet-app-<stamp>.tar.gz` versioned 사본 보존(rollback.sh 실효성 복원)
- **Infra H1**: frontend build도 `compose down` 이전으로 이동(빌드 실패 시 라이브 outage 차단)
- **Infra CR2**: backend lifespan startup task `carry_forward_backfill_all(only_missing=True)` — 0028/0029 alembic noop + 운영자 수동 호출 누락 영구 차단
- **Tesla H1**: `settings._validate_signals_against_tesla` + `settings.repush_all` 두 곳에 `prefer_typed: true` 추가(onboard.register와 일관)
- **FE H1**: customers handler 3종(remove/removeAll/add) `selectedIdRef` capture-and-compare 패턴 — await 도중 다른 고객사 선택 race 차단
- **FE H2**: `/vehicles` `customerNameById` inline `new Map(...)` → `useMemo`로 식별자 안정화(FleetVehicleList 매 render 재렌더링 방지)

**신규 endpoint (Customer CRUD, Alembic 0030)**:
- `GET    /customers` — 전체 고객사 + `vehicle_count`
- `POST   /customers` — 생성 (body: `{name: str}`). `name` UNIQUE → 409
- `GET    /customers/{id}` — 단건 + `vehicles[]` inline (관리 화면용)
- `DELETE /customers/{id}` — vehicles 0건일 때만 허용(409 가드)
- `POST   /customers/{id}/vehicles` — 차량 일괄 추가(body: `{vehicle_ids: UUID[]}`). 다른 고객사 소속이면 그쪽 customer_id 덮어씀 *(v1.5.x에서 silent override 제거 → 409 Conflict + 충돌 vid 리스트 반환으로 변경됨, 아래 v1.5.4/v1.5.5 항목 참조)*
- `DELETE /customers/{id}/vehicles` — 차량 일괄 제거(같은 customer_id만 NULL SET)

**신규 endpoint (carry-forward 관련)**:
- `GET  /vehicles/{id}/latest` — `vehicles.latest_telemetry` JSONB snapshot 직접 반환
- `POST /vehicles/{id}/refill-latest-snapshot` — admin용 차량별 carry-forward backfill(컬럼별 subquery + jsonb concat). 0028/0029 alembic noop 잔존 데이터 보완. 2026-06-10: 서브쿼리를 최근 10만 행 시점으로 bound(all-NULL 컬럼 풀스캔 방지) + 결과를 기존 snapshot에 **merge**(`jsonb_strip_nulls` — cutoff보다 오래된 희소 컬럼 값 보존, '교체'가 아닌 '보강'). daily_scheduler가 only_missing=True로 일일 위임 실행

**응답 스키마 변경**:
- `VehicleListItem.customer_id?: UUID | null` 추가
- `GET /vehicles` 쿼리에 `?customer_id=<uuid>` 필터 추가

**Backend (carry-forward 패턴, 100회 검토 fix)**:
- `handle_telemetry` E1/E2: row 원본 sparse INSERT + snapshot atomic `jsonb ||` UPSERT + WHERE ts 가드 DB level
- `_ingest_one_dump`: vin별 carry-forward accumulator + atomic UPSERT(seed 적재 경로). 시작 시 `SeedImport(status='in_progress')` 즉시 INSERT — crash 후 retry 중복 적재 차단
- OAuth scopes에 `vehicle_location` 추가(Tesla 2024 후반 분리, GPS/속도/Shift 차단 위험 해소)
- Tesla pairing URL: `https://tesla.com/_ak/<domain>` (공식)
- `KEY_TO_COLUMN` Tesla proto Field enum 정합: Power→ACChargingPower/DCChargingPower, IsClimateOn→HvacACEnabled, IsPreconditioning→DefrostForPreconditioning, TpmsHardWarnings 단일

**Frontend**:
- 메인 현황(`/`): 3분할(좌 차량 1열 + 가운데 지도 + 우 summary). VIN pill AdvancedMarker(anchorPoint BOTTOM, 줌 안정). 차량 선택 시 panTo. 차량 카드에 고객사명 Badge.
- 차량 정보(`/vehicles`): Select 고객사 필터 + 선택 고객사 차량 지도(MainFleetMap dynamic). 모바일 백버튼.
- 차량 상세(`/vehicles/<id>/`): 8 상태 섹션 2열 grid + 그래프(SectionTimeline) 제거. 기타 신호 hover tooltip.
- 고객사 관리(`/admin/customers`): 등록 form + 좌 목록 + 우 관리. Checkbox emerald(추가)/rose(제거) 색 명확. '+ 차량 추가' Dialog. 다른 고객사 소속 차량은 disabled + 이름 Badge.
- shadcn Sheet/Dialog/Card/Checkbox/Select/Badge/Button/Input/Label 활용

**Infra**:
- Alembic을 backend Dockerfile CMD에서 분리 → `deploy.sh`가 `compose down` **이전** one-shot 실행(실패 시 라이브 outage 회피)
- backend CMD에서 `python -m app.seeds.dummy` 제거(SEED_ON_STARTUP=1로만)
- depends_on 4건 `service_healthy → service_started`, healthcheck `start_period 60s retries 6`
- mem_limit 조정: consumer/archiver 192→256m, frontend 256m, backend 480m, nginx 64m (합 1184→1312m, t2.small 안전)

**해소됨**: ✅ BE telemetry_events UNIQUE(0040 `uq_te_vehicle_ts_payload` + ON CONFLICT) · ✅ customers 인증(require_admin, 2026-06-10). **잔여 deferred**: customer FK RESTRICT, Tesla TpmsHardWarnings tire_location_value 분기, Preconditioning 의미 재정의.

---

### v1.5.8 — Replay 검증 + kafka_consumer batch 가속 + RDS 업그레이드 (2026-05-28) — alembic head **0034**

> v1.5.7 이후 3 commit. **alembic head 0034 유지**(스키마 무변경). **API 표면 무변경** — 환경변수 / 인프라 / 운영 도구 위주 변경. 라이브 검증: 2025년 데이터 13.6M lines lossless Iceberg 적재 + DB INSERT 80/s → 1,500/s 가속.

**Backend — kafka_consumer batch 처리 (E)**:
- `process_v_batch_optimized` 신규 추가 — batch 시작 시 vehicle별 `latest_telemetry` + `last_event_at` 한 번에 SELECT(in-memory map) → vehicle별 ts ASC 정렬 → progressive carry-forward(cur_snap 점진 갱신) → telemetry_events bulk INSERT(executemany 패턴, raw_data dict→JSON 직렬화) → vehicle 메타 vid별 1회 UPDATE(`event_count += N`, case로 first/last_event_at min/max) → latest_telemetry는 batch 내 max ts 메시지의 final snap만 jsonb concat
- **bulk INSERT 실패 시 single fallback** — SAVEPOINT per-message 격리 보존(poison message 1건이 batch 전체 abort 안 함)
- **정확성 100% 동일** — 단건 처리와 결과 비트 단위 일치
- **효과**: 80/s → 800-1,500/s (10-18x), replay catch-up 6일 → ~3시간

**신규 환경변수**:
| 변수 | Default | 의미 |
|---|---|---|
| `KAFKA_MAX_RECORDS` | `1000` | batch 1회 최대 메시지 (이전 hardcoded 100) |
| `CARRY_FORWARD_FORCE` | `0` (live) / `1` (replay) | forward-only ts 가드 우회 — replay는 메시지 ts가 과거(예: 2025-02)라 가드에 막혀 carry-forward skip되는 문제 해결 |
| `VEHICLE_CACHE_MAX` | `10000` | VIN→vehicle_id in-process cache cap (FIFO eviction) |

**Infrastructure — RDS 업그레이드 → 단계적 다운그레이드**:
- catch-up: `db.t4g.micro` → `db.t4g.large` (1→2 vCPU, 1→8GB RAM) — kafka_consumer batch와 함께 가속용
- Terraform 신규 옵션: `infra/modules/database/variables.tf` `apply_immediately` (default false, true 시 즉시 적용 ~3-5min 다운타임)
- 다운그레이드: catch-up 후 `db.t4g.large` → `db.t4g.medium`(2026-05-28) → **`db.t4g.small`**(2026-05-29, 일상 저부하 확인) — 누적 월 -$73
- `infra/envs/dev/terraform.tfvars`: `rds_instance_class = "db.t4g.small"` + `rds_apply_immediately = false` (2026-06-01 클래스 변경 작업 종료 후 false 복귀 — 무관 apply의 의도치 않은 즉시 다운타임 방지)
- 실 다운타임 각 3분. ⚠ small(2GB)은 RAM 여유 적음 — 대량 적재/replay 시 medium+ 복귀 권장

**Operations — 2025 데이터 replay 검증 (2026-05-27 → 2026-05-28)**:
- 도구: `backend/scripts/replay_s3_to_kafka.py` (v1.5.7에서 준비, v1.5.8에서 라이브 실행)
- tesla_V/2025: 17,824 객체 / 13.6M lines / 30,269s (8.4h publish) / **0 errors** / DLQ baseline=5 변동 없음
- Iceberg sink: `totalRecords = telemetry.raw.v1 offset` (15,388,695, **100% lossless**), 118 Parquet files, 1.05GB
- DB INSERT catch-up: kafka_consumer batch 가속으로 ~3-7시간 진행 중
- **2025 데이터에 5 VIN(5YJ3E1EA*/5YJ3E1EB*/LRWYGCFJ6SC106354)은 alerts만 존재** — tesla_V 메시지 없음. vehicle row + vehicle_alerts 정상 적재, telemetry_events=0 (정상)

**Documentation (3 파일)**:
- `DB_SCHEMA.md` header alembic 0033 → 0034, RDS db.t4g.large 명시 + §2.9 seed_imports CHECK 확장 + §4 마이그 이력 0034 행
- `API_REFERENCE.md` §6.1 환경변수 확장 — kafka_consumer / s3-archiver / Bronze pipeline 적재 경로
- `AWS_SETUP_GUIDE_BEGINNER.md` §3 인프라 표 갱신(kafka_connect EC2 + Glue Catalog + RDS t4g.large) + §15.3 Bronze envelope 토픽 + **§15A Iceberg Bronze Sink 검증** (Connect 상태, connector, Glue+S3 Parquet, DLQ) + §19.12 Bronze pipeline 운영 + §19.13 kafka_consumer batch + §19.14 S3 replay 도구 + §19.15 RDS instance class 변경

**deferred (Phase B)**:
- Bronze Replay UI (alembic 0035 `replay_imports` + backend `/admin/bronze-replay/*` + FE `BronzeReplayManager.tsx`) — catch-up 완료 후
- Kafka lag 표시 UI (메인 status card, `/api/v1/admin/kafka-lag` AdminClient 기반) — catch-up 완료 후
- 5 VIN UX 개선 (alerts only 차량 시각적 구분) — catch-up 완료 후 결정

---

### v1.5.7 — 10번째 정밀 검토 ×4 agent + 사용자 보고 fix 다수 (2026-05-27) — alembic head **0034**

> v1.5.6 이후 누적 12 commit. **alembic head 0034 유지**(스키마 무변경). 회귀: tsc clean + next build PASS. Tesla 공식 API 정합 10회차 — 9회차 deferred 일부 해결 + 신규 CR/H fix.

**UI 신규 기능 + 사용자 보고 fix**:
- **차트 크게보기 / 원상복구 토글** — 차트 우상단 Maximize2/Minimize2. 클릭 시 그 차트만 xl:col-span-2 + 세로 1.5배(`h-[16.5rem] sm:h-96`), 나머지 차트는 mount 안 함(완전 숨김). localStorage 영속(`teslafleet_enlarged_chart`). 한 번에 하나만 enlarged.
- **지도 마우스 휠 zoom 차단** — `scrollwheel={false}` (VehicleRouteMap + MainFleetMap). 버튼 + 터치 핀치만 zoom. drag/팬 정상.
- **MainFleetMap zoomControl 명시** — mapId 사용 시 default UI에서 자동 노출 안 되던 +/− 버튼 회복.
- **vehicles 페이지 React #300 무한 update fix** — URL sync useEffect deps `[searchParams]` → primitive `[fromParam, toParam, daysParamRaw]` (useSearchParams 매 render 새 reference 가능성 차단) + lastDays NaN 가드(`days=foo` 같은 invalid 값 시 `NaN !== NaN` 무한 fetch 루프 차단).
- **a5268265 차량 페이지 events 17초 cold** — events `total <= limit` 분기에 캐시 적용 → 두 번째 호출부터 ms.
- **error.tsx 상세 노출** — error.message(200자 제한) + digest details 토글 추가.

**10회차 audit fix (CR 4 + H 7 + M 9)**:

| ID | 영역 | 핵심 |
|---|---|---|
| **FE CR1** | VehicleDashboard | `enlargedChartId` localStorage stale 검증 — CHART_DEFS에 없는 id면 dead state(6 차트 모두 null) → 검증 후 정리 |
| **BE CR1** | vehicles | 30s 캐시 무효화 부재 → customers add/remove 30s stale → `invalidate_vehicles_cache()` helper + 2 위치 호출 |
| **Infra CR1** | nginx | onboard host /api/ Basic auth 우회 → 라이브 VIN/GPS/고객 데이터 노출 → `$api_basic_auth`(sphere+onboard) + `^~ /api/v1/onboard/` 차주 페어링만 무인증 |
| **Infra CR2** | nginx | catch-all `server_name _;` + EC2 IP 직접 hit → 임의 Host로 우회 가능 → `default_server return 444` + `server_name` 명시 host만 |
| **Tesla CR1** | settings | `_validate_signals_against_tesla` task race(연타 PUT → 차량 3-config cap 소진) → `asyncio.Lock` + 30s cooldown |
| **Tesla H1** | partner | `PARTNER_SCOPES`에 `offline_access` 추가(owner scope superset) |
| **Tesla M3** | sim | `gen_charging_state` enum prefix(`Complete` → `ChargingStateComplete`) — `_strip_enum_prefix` 일관 |
| **Tesla M5** | seed | `tireLocationValue` camelCase + snake_case 양쪽 시도 |
| **BE M1** | seed | cooldown `status != 'in_progress'` PG NULL 회피 → `is_distinct_from`(2 위치) |
| **FE H1** | error.tsx | message 200자 제한(긴 stack/민감 정보 누출 완화) |
| **FE H2** | LayoutShell | MutationObserver `subtree: true` — 깊은 자식 변경 anchor 보정 |
| **FE H3** | VehicleDashboard | floating timeline 모바일 max-h 80vh → 40vh(본문 가림 완화) |
| **FE M1** | vehicles/page | days `Math.floor` — 소수값 정수로 BE 송신 |

**deferred 유지**:
- BE H2 cache stampede(per-key inflight Future) — 운영 부하 한정적, deferred.
- BE M3 GPS fallback stale(kafka_consumer invalidate) — 30s TTL로 운영 적정.
- BE H1 events cache hit/miss 응답 타입 일관성(Pydantic 재검증 비용 최적화).
- Tesla H3 fleet_telemetry_config 응답에 `error` 필드 파싱.
- Tesla H4 Semi `tireLocationValue` trailer/steer — 현재 Model 3/Y 운영 무영향.
- Tesla M1 Retry-After HTTP-date 처리 / M6 `validation_target_vin` 운영자 지정.
- 기존: BE H2 PKCE / H3 Region 분기 / M3 id_token JWKS / event_stats race / Dockerfile SHA digest / CloudWatch alarm / 외부 monitoring / 8443 mTLS rate limit / RDS CMK / CloudFront Authorization forward 등 Phase 9.

---

### v1.5.6 — 9번째 정밀 검토 ×4 agent + 사용자 보고 fix 다수 (2026-05-26) — alembic head **0034**

> v1.5.5 이후 누적 11 commit. **alembic head 0034 유지**(스키마 무변경). 회귀: tsc clean + next build PASS. Tesla 공식 API 정합 9회차 — H 3 deferred(KR 단기 영향 없음, Phase 9 처리).

**UI 신규 기능**:
- **타임라인 컨트롤 표시 모드 토글** — sticky(Pin) / inline(Move) / floating(PinOff) 3-way cycle. localStorage 영속(`teslafleet_timeline_mode`). 차량 정보 카드 우상단 아이콘 버튼. floating은 화면 우하단 카드(rounded-xl + shadow-2xl + backdrop-blur-md). i18n ko/en 5키.

**사용자 보고 fix(누적 8건)**:
- chip click 버그 3건: events 로드 전 무동작 / `to=maxTsLocal` 고정으로 새 데이터 안 보임 / "전체" 좁아짐 — `now` 기준 계산 + URL `days=N`만 박음.
- 경로 fetch race(자동 days=1 변경) → AbortController + lastDays 결정 로직 명시 + edge case 보완.
- 새로고침/chip 변경 시 "텔레메트리 데이터가 없습니다" 회귀 → URL `?days=N`만 박아 BE `last_days` max_ts 기준 → stale 차량도 데이터 보장.
- 경로 응답시간 10.9s → cold 5.16s / warm 0.15s — `width_bucket` 단일 쿼리 + 60s TTL 캐시 (events 패턴).
- 스크롤 영역 layout 변동 시 viewport 흔들림 → ResizeObserver+MutationObserver `usePreserveScrollAnchor` hook(viewport 30% 위치 anchor 기준 scrollTop 보정). main + vehicles section 양쪽 적용.
- sticky/inline 시각 동일 회귀 → `overflow-x-hidden` → `overflow-x-clip`. iOS 15 fallback @supports.

**9회차 BE/Infra audit fix**:
- BE perf: `/vehicles` 5.97s → 0.17s warm — DISTINCT ON GPS fallback에 30s TTL LRU 캐시.
- BE H4: `route_by_vehicle` PG width_bucket 빈 base CTE NULL row 가드(`ts/lat/lng` NULL 필터).
- BE H6: seed cooldown self-block — `_resolve_or_reject_in_flight` 후 자기 자신이 in_progress 상태로 cooldown 차단. `status != 'in_progress'` 추가(2 위치).
- FE CR1: handleChipClick input 자동 클리어 회귀 — URL sync useEffect를 days param 기반 자동 채움(URL=source of truth, input=derived).
- FE CR2: Play RAF effect deps에 `showDataTable` 누락 race — deps 추가.
- FE H1: scroll handler rAF debounce (layout thrash 회피).
- FE H2: vehicles/page.tsx section scroll context에도 `usePreserveScrollAnchor` 적용(`SectionWithAnchor` wrapper).
- FE H3: `overflow-x-clip` iOS 15 fallback(`@supports not (overflow: clip)`).
- FE H4: denseRoute cleanup `setDenseRoute(null)` 추가 — 범위 변경 시 stale polyline 차단.
- Infra CR3: sphere host `/api/` Basic auth 우회 차단 — `/api/`/`auth/`에 `auth_basic $sphere_basic_auth`. OAuth callback exact match만 off(Tesla redirect target, state+rate limit 보호).

**deferred 유지/추가**:
- Tesla H1 PKCE / H2 authorize audience / H3 Region 자동 분기 — KR 단기 영향 없음, Phase 9.
- Tesla M2 401 자동 refresh-and-retry / M3 id_token 서명 검증(JWKS) / M5 settings validate Tesla throttle.
- BE M5 telemetry.py `latest_event_by_vehicle` dead code 검토(vehicles.py에 동등 endpoint).
- BE M2 kafka_consumer `_SKIP_CARRY_KEYS` 모듈 상수화.
- FE M1 `SectionTimeline`/`CHART_COLOR_BY_KEY` dead code(~90줄).
- FE M3 `cycleTimelineMode`의 localStorage setState updater 외부 이동(StrictMode 중복 회피).
- FE M4 floating mode 페이지 하단 safe-area-inset 보정.
- FE M5 Promise.all events/alerts에 AbortSignal 전달.
- FE M6 `currentPoint` useMemo(VehicleRouteMap Marker re-render).
- FE M7 `sortedEvents` sort Date alloc 최적화.
- 기존: BE event_stats race / _INPROGRESS_STALE_SEC 60s vs 대용량 file / _ingest_one_dump marker_inserted=False dead code / Tesla wake_up/fleet_telemetry_config_get/errors endpoint / Dockerfile SHA digest / CloudWatch retention / 외부 monitoring / 8443 mTLS rate limit / RDS CMK / container hardening / sphere host IP-bypass.

---

### v1.5.5 — 8번째 정밀 검토 ×4 agent + UI/Seed/Carry-forward 다수 (2026-05-26) — alembic head **0034**

> v1.5.4 이후 누적 ~20 commit. **alembic 0034 신규**(seed_imports.status CHECK에 'in_progress' 추가). 회귀: tsc clean + next build PASS + pytest 207 (4 new test 추가). Tesla 공식 API 정합 8회차 검토 — 위반 0건.

**UI 신규 기능**:
- 차량 상세 **기간 필터 시간(HH:MM) 단위** — TimeField (`<input type="time">` step 60 native picker) + start/end 페어. ISO 변환 `T${HH:MM}:00`/`:59.999` 로컬 TZ. 빈 time default `00:00`/`23:59`. 같은 날 start>end disable.
- **데이터 보기 layout shift 0** — '불러오는 중' 메시지 visibility 토글(h-5 mb-2 고정), dataAtTs prev 유지(close/network err만 null reset). 섹션 height 변동 없음.
- **재생 sync 모드** — `showDataTable` 열린 채 재생 시 시간 기반 RAF 미동작. dataAtTsLoading false 떨어지면 다음 idx로 chain. 항목당 1초 최소 보장(MIN_TICK_MS=1000, idxStartTimeRef stale on Play start fix).

**Seed (CR-grade race fix + endpoint)**:
- `alembic 0034` — `seed_imports.status` CHECK에 'in_progress' 추가. v1.5.x에서 `_ingest_one_dump`가 시작 시 in_progress 마킹 패턴 도입했으나 0019 CHECK가 ('completed', 'failed')만 → 모든 INSERT CheckViolationError → 사용자에게 "concurrent ingest" 메시지로 표시되던 영구 차단 해소.
- `_ingest_one_dump` **ON CONFLICT DO UPDATE** — PG: stale row(failed / completed empty / in_progress ≥60s) 강제 점유, 정상 completed/recent in_progress 보호. SQLite 단순 INSERT fallback.
- `_INPROGRESS_STALE_SEC = 60s` (5분→1분) — 사용자 abort 후 즉시 회복.
- **POST `/admin/seed/reset-in-progress`** 신규 endpoint — 운영자 강제 cleanup(prefix LIKE).
- `list-month-files` 응답 **4-way 분류** — `already_loaded` + `retry_breakdown.{failed, empty, stale_in_progress}` + `active_in_progress` + `new_count`.
- 8회차 BE H1: ingest-one tz-naive 비교 TypeError — `existing.loaded_at.tzinfo is None → UTC` 정규화.

**Carry-forward (옵션 A — DB write 시점 dense INSERT)**:
- `_init_vin_snap_from_vehicle` — `vehicles.latest_telemetry` JSONB → snap dict(timestamp는 `__ts` parse). 8회차 FE/BE fix로 forward-only ts 가드 + tz-naive 정규화.
- `_ingest_one_dump`: file 안 stream carry-forward + inter-file lazy init.
- `kafka_consumer.handle_telemetry`: prev_latest JSONB → 매 message NULL 컬럼 채움. SQLite tz-naive 가드.
- Tesla 정합: raw_data 원본 보존 (carry-forward skip 키), forward-only ts 가드 — out-of-order 옛 row sparse 유지.

**Customers (silent override 정책 reverse)**:
- backend `POST /api/v1/customers/{id}/vehicles` — 다른 고객사 차량 추가 시 **409 Conflict** + WHERE customer_id IS NULL 가드.
- frontend addCandidates `customer_id === null` 필터 (미배정만 표시).

**Sphere Basic auth**:
- `nginx.conf` map `$host $sphere_basic_auth` — `sphere.tesla.modapl.dev`만 realm, 그 외 host (onboard / health / api / .well-known) off.
- `deploy.sh` Secrets Manager `/teslafleet/sphere-dev/basic-auth` → openssl passwd -apr1 → htpasswd 자동 생성.
- terraform `infra/envs/dev/main.tf` IAM v8 동기 (basic-auth + tesla-partner-public-key.pem ARN 명시).

**컬러 모드 / shadcn / 기타 UI**:
- 7 컬러 모드 WCAG AA 24건 fix (globals.css 토큰 + 9 컴포넌트 semantic warning/success/destructive/accent-foreground)
- shadcn 활용 강화 (Badge/Alert/Button/Card asChild) + 회귀(Card override / Alert grid) inline div 복원
- 메인 현황 통계 섹션 (고객사/차량/이벤트 — Intl compact)
- FleetVehicleList 고객사명 정렬 + 카드 event_count
- 차량 정보 상세 row chart popup (6 필드, Dialog size="large")
- 시뮬 KOREAN_CITIES 28도시 ± jitter
- AppBar 활성 항목 클릭 차단
- Maps minZoom=3 world wrap 방지

**8회차 audit 새 fix**:
- FE H1: idxStartTimeRef stale on Play start — useEffect로 Play 토글 시점 ref 갱신
- BE H1: ingest-one tz-naive 비교 TypeError 정규화
- BE M1~M4: list-month-files tz 정규화 / 주석 stale / types.ts retry_breakdown 누락 / _init_vin_snap __ts 정규화 강화
- Infra CR1: terraform IAM v8 동기 (drift 방지)
- Infra CR2: nginx 정적 자산(`/assets/`, svg/png/...) outer add_header reset 회복 — X-Frame/X-Content-Type/CSP/HSTS/Referrer/Permissions 명시 재선언

**deferred 유지**:
- BE event_stats race (큰 마이그 회피)
- _INPROGRESS_STALE_SEC=60s vs >60s 대용량 file ingest duplicate 위험 (보통 수 초 — 운영 영향 적음)
- _ingest_one_dump `marker_inserted=False` dead code (ON CONFLICT 도입 후 도달 불가)
- Tesla `wake_up`/`fleet_telemetry_config_get`/`fleet_telemetry_errors` endpoint (운영 진단용)
- PKCE / Region(EU/CN) 자동 분기
- Dockerfile SHA digest / CloudWatch retention / 외부 monitoring / 8443 mTLS rate limit / RDS CMK / container hardening — Phase 9
- sphere host IP-bypass(EC2 80 직접 hit) — design intent (CloudFront 앞단 + API 별도 auth)

---

### v1.5.4 — 7번째 정밀 검토 ×4 agent + UI/UX 다수 (2026-05-22) — alembic head **0033**

> v1.5.3 이후 누적 9 commit (UI 신규 기능 6 + agent CR/H fix). alembic head 0033 유지(스키마 무변경).
> 회귀: tsc clean + next build PASS + pytest 199 passed (1 pre-existing aiosqlite race, BE deferred). Tesla 공식 API 정합 검증 — 위반 없음.

**UI 신규 기능 (사용자 요청)**:
- 메인 현황 차량 목록 상단 **통계 섹션**(고객사/차량/누적 이벤트) — Intl.NumberFormat compact 포맷, 한/영 자동 분기
- FleetVehicleList **고객사명 정렬** — localeCompare(locale, sensitivity:'base'), 미배정 차량은 별도 bucket으로 list 끝
- 카드에 **이벤트 수** 표시 — Activity 아이콘 + fmtInt
- 차량 정보 상세 '선택 시각의 상태' **6 필드 차트 팝업** — Dialog (size="large" h-[60vh] max-h-[640px] min-h-[320px], max-w-5xl). 부모 슬라이더와 cursor 동기. 고도/실내·외기 온도/타이어 4륜/종방향·횡방향 가속도
- 시뮬 시작 좌표 **KOREAN_CITIES 28도시** (남한 20 + 북한 8) ± 0.02° jitter
- **AppBar 활성 항목 클릭 차단** — preventDefault + aria-disabled + tabIndex=-1 + cursor-default
- Maps `minZoom={3} maxZoom={20}` — world wrap 방지

**Customers add 정책 변경 (CR-grade)**:
- backend `POST /api/v1/customers/{customer_id}/vehicles` — 다른 고객사 차량 추가 시 **409 Conflict** (이전 silent override 제거)
- `UPDATE WHERE customer_id IS NULL` 가드로 멱등 재추가(같은 customer_id) OK + race condition 안전
- frontend addCandidates `v.customer_id === null` 필터로 미배정 차량만 dialog 표시
- 정책: 다른 고객사 차량 이동은 명시적 2단계 (원 고객사에서 먼저 제거 → 미배정 → 신규 고객사 추가)

**a11y / 컬러 모드 (CR-grade)**:
- 7 컬러 모드 WCAG AA contrast **24건 fix** — globals.css 토큰 조정 + 9 컴포넌트 semantic warning/success/accent-foreground
- light/sepia `text-warning` 본문 대비 2.94/3.14 (AA 실패) → L 0.68→0.54, sepia L 0.62→0.50 + foreground swap (AA 5.28/5.24+ 통과) — v1.5.4 7th audit FE CR4
- Dialog `max-w-5xl/2xl` sm+에서 shadcn `sm:max-w-lg` 잔존 회귀 → `sm:max-w-...` 명시 — FE CR1/CR2
- '선택 시각의 상태' row chart 버튼 hover `text-foreground` → `text-accent-foreground` (hc/oled 1.6 대비) — FE CR3
- Dialog short viewport(<700px) clip → `max-h-[90vh] overflow-y-auto` — FE H1
- not-found 정적 export 한/영 병기 (I18nProvider 외부)

**Backend / Tesla 정합**:
- BE H1 repush-all owner-level `tesla_request /products` try/except wrap — 한 owner 네트워크 에러 시 전체 endpoint 500 회피, cooldown 소모 방지
- BE M1 onboard `_fetch_fleet_status` docstring 'GET' → 'POST' (v1.5.x CR2 fix 후 doc drift)
- Tesla 정합 — 6th audit fix(H1/H2/M1) 이후 잔존 결함 0. 7th audit에서 9 영역(OAuth/partner_accounts/products/fleet_status/fleet_telemetry_config/streaming/error retry/region) 모두 spec 정합 확인

**Infra**:
- Infra H1 `docker/fix-env.sh` deploy.sh와 secret 세트 동기화 — 누락 3종(GOOGLE_MAPS_API_KEY / NEXT_PUBLIC_GOOGLE_MAPS_API_KEY / TESLA_PARTNER_PUBLIC_KEY_B64) 보강 + umask 0077 + fail_on_empty 인자 + DEPLOY_STAMP 일관
- Infra H2 `docker/rollback.sh` — DEPLOY_STAMP build-arg(`rollback-<ts>`) + `--wait --wait-timeout 120` + build down 이전 분리

**shadcn 활용 강화 + 회귀 보완**:
- Badge/Alert/Button/Card/asChild — 10 파일에 적용
- 일부 회귀(Card override `p-N + py-0` padding 충돌 / Alert `bg-card` tint 잃음 / AlertTitle `line-clamp-1` 한국어 헤딩 잘림) — inline `div bg-{kind}/10` 복원 (role="alert" 보존)
- 수치 표기 `truncate(…)` 잘림 → `break-all` wrap (VehicleSummaryPanel Row / VehicleDashboard 선택 시각의 상태 / raw_data row)

---

### v1.5.3 — 100회 검토 ×6 결과 안전 fix (2026-05-22) — alembic head **0033**

> 5번째 검토 deferred 청산 + 새 발견. **alembic head 0033 유지(스키마 무변경)**. tsc clean + next build PASS + pytest 199/200(1 pre-existing aiosqlite race, BE deferred).

**Infra (CR1 + CR2 + CR3 + H1 + H4 + H7 + H8 + M1 fix)**:
- CR1 — `deploy.sh` DEPLOY_STAMP build arg → image LABEL (Dockerfile `LABEL deploy_stamp=$DEPLOY_STAMP`) — 캐시 영향 없음, 빌드 추적 가능
- CR2 — `deploy.sh` `docker compose build … | tail -10` 빌드 실패 시 앞쪽 stderr 누락 회복 — 전체 로그 dump + 실패 시 cat
- CR3 — `disk-cleanup-setup.sh` 매 deploy `systemctl daemon-reload` 호출 churn(시간당 4~9회 deploy) → unit 파일 hash 변경 시에만 reload
- H1 — backend `mem_limit` 480→640m + `mem_reservation` 240→320m (lifespan + carry-forward backfill 동시 시작 시 swap-out lat spike 방지)
- H4 — frontend Dockerfile `ENV NODE_OPTIONS=--max-old-space-size=1536` — Next.js 15 build OOM (t2.small 2GB 5 컨테이너 공유)
- H7 — `deploy.sh` + `fix-env.sh` `aws secretsmanager get-secret-value` transient 5xx/throttle 시 빈 값 `.env` 생성 → backend startup 실패. 5x 지수백오프(1+2+4+8+16s = 총 31s)
- H8 — nginx rate limit zones: `limit_req_zone $binary_remote_addr zone=api_zone:10m rate=60r/s` burst 120 + `auth_zone:10m rate=10r/s` burst 20. 0.0.0.0/0 SG 노출 1차 방어. webhook 8443 mTLS는 별도 SG (telemetry-sg) 작업
- M1 — `.env.example` DATABASE_URL 평문 예시 misleading → SECRET_ID-기반 패턴 명시 + override 옵션

**BE (H1 + H2 + M1~M5 fix)**:
- H1 — Simulator `RICH_SIGNAL_CATALOG`가 deprecated Tesla 키 10개(Power/UsableBatteryLevel/ChargingPower/ChargerActualCurrent/BatteryRange/IsClimateOn/IsPreconditioning/VehicleState/TpmsHardWarning{Fl/Fr/Rl/Rr}) 송신 — KEY_TO_COLUMN 미존재로 typed 컬럼 NULL + raw_data fallback. **공식 enum(ACChargingPower/HvacACEnabled/PreconditioningEnabled/TpmsHardWarnings tireLocationValue)** + legacy alias 보존
- H2 — `kafka_consumer.handle_telemetry` SQLite fallback path `prev_ts(naive) >= ts(aware)` TypeError. PG는 timestamptz로 항상 aware라 운영 영향 0이나, 테스트 환경 회귀 가드. UTC 정규화 분기 추가
- M1 — `main.py` dead import (`from fastapi.testclient import TestClient`) 제거
- M2~M5 — test fixture 정합 (VIN 17자 / `_seed_events` 단일 row / invalid prefix `bulk-sim:all` / Tesla deprecated 키 정합 unit test 갱신)

**Tesla 정합 (H1 + H2 + M1 fix)**:
- H1 — `settings._validate_signals_against_tesla` Tesla 응답 raw text를 `telemetry_config_signals.last_validation_error`에 **평문 저장** → Tesla가 응답에 Authorization echo 시 token이 DB+admin UI 노출. `safe_response_text(text, limit=N)`로 JWT/access_token/refresh_token/id_token 필드 마스킹 후 저장
- H2 — `_get_access_token` implicit refresh 시 `token.scopes` 갱신 누락 → 사용자가 Tesla 계정에서 scope 추가/제거 후 첫 API 호출이 implicit refresh면 stale scope DB 영구. auth.py 동일 패턴(string/array 분기)으로 정합
- M1 — `auth.login()` OAuth authorize URL에 `audience` 누락(token endpoint는 보냄) → cross-region 운영 시 token 잘못된 region 발급 위험. NA-only 환경은 무영향(NA→NA), 미래 region 확장 대비

**FE (H1 + H2 + M1 + M2 fix)**:
- H1 — `fetchReverseGeocode` 동시 N개 호출(메인 페이지 3 mounted VehicleSummaryPanel + N FleetVehicleList card) → cache hit 전까지 N개의 외부 Google API call. **in-flight Map (`_GEOCODE_INFLIGHT`)** 첫 promise 공유 + 호출자별 AbortGate(`_attachAbortGate`)로 abort 분리
- H2 — `TelemetryChart` 다크 테마 감지 `dark` 클래스만 검사 → hc/solarized/nord/oled 4개에서 light palette → canvas grid/axis 거의 안 보임. `_DARK_THEME_CLASSES` 5개 어두운 테마 모두 dark palette
- M1 — `LayoutShell h-screen`(100vh) → `h-dvh`(dynamic) — iOS Safari URL bar collapse 시 layout shift
- M2 — `admin/customers` sticky '← 차량 목록' 잔존 일괄 제거 (5번째 라운드 4개 화면 정리에서 누락)

---

### v1.5.2 — 100회 검토 ×5 결과 안전 fix (2026-05-21) — alembic head **0033**

> **5번째 100회 검토(4 agent 병렬)**: CR 2 + H 10 + 인프라 강화 + Tesla API 정합.

**Critical (즉시 운영 차단 → 라이브 fix)**:
- **BE CR1** (`auth.py:113-143`): callback `granted` 변수 정의 순서 오류로 **모든 OAuth callback UnboundLocalError → 500**. 로그인 자체 차단 상태였음. 변수 계산을 DB write 진입 전으로 이동.
- **Tesla CR2** (`onboard.py:67-82`): `fleet_status` 호출이 Tesla 공식과 불일치 — GET + query string → **POST + JSON body**. 이전 호출은 400/405로 항상 빈 응답 → 모든 차량 paired=null 표시 회귀. Tesla 공식 spec 일치 복원.

**Backend H 5건 fix**:
- H2 (`vehicles.py:286`): `_carry_forward_one_vehicle` UPDATE의 `last_event_at = :ts` → `IS NOT DISTINCT FROM :ts` (NULL=NULL 비교 가능, resync race silent loss 차단)
- H5 (`auth.py:128-141`): Tesla scope 응답이 array일 때 분기 추가 (string + array 둘 다 처리)
- H6 (`seed.py:870-878`): event_stats cache write 시점에 expired entries sweep — 무한 grow 차단
- H10/M1 (`vehicles.py:80-99`): `ANY(:vids)` → `ANY(CAST(:vids AS uuid[]))` asyncpg type binding 명시. fallback exception에 logger.warning 추가

**Tesla API 정합 3건 fix**:
- H6 (`streaming_sample.py:226`): `DefrostForPreconditioning` KEY_TO_COLUMN 매핑 제거 — `PreconditioningEnabled`(광의)만 `is_preconditioning` 컬럼 매핑. 두 신호 동시 송신 시 last-wins 비결정 회귀 차단(좁은 의미 신호는 raw_data 보존)
- H11 (`register_partner_account.py:32`): partner token scope에 `vehicle_location` 추가(차주 OAuth scope와 정합)
- M5 (`streaming_sample.py:301-309`): TpmsHardWarnings Semi 트레일러/스티어 추가 키를 `raw_data.TpmsHardWarnings_extra`로 보존(이전 무시되던 데이터 손실 차단)

**Frontend H 2건 fix**:
- H1 (`VehicleDashboard.tsx:594-636`): RAF visibility 보정 — 백그라운드 탭에서 `performance.now()` 단조 흐름으로 visible 복귀 시 progress jump → 즉시 종료 회귀 차단. `visibilitychange` listener로 hidden 시간 offset playStartRef 보정
- M1 (`admin/customers/page.tsx:194-218`): `handleSaveEditName` early-return 전 editingName clear + refresh — race 도중 다른 고객사 클릭 시 stale UI 잔존 차단

**Infra CR2 + H3 fix**:
- CR2 (`disk-cleanup-setup.sh`): prune 윈도 48h → **24h** + `docker buildx prune --filter "until=24h"` 추가 (BuildKit cache는 system prune 외부 저장). disk full incident 2026-05-21 재발 차단
- H3 (`deploy.sh:139-150`): `docker compose up -d --wait --wait-timeout 120` + `docker compose ps` 검증 — 한 컨테이너라도 running 아니면 명시 exit 99 + 로그 출력 (이전: silent success)

**Deferred (운영 결정 / 큰 변경 필요)**:
- ~~Infra CR1 (build cache 결정성), CR3 (daemon-reload churn), H1 (mem_limit 480m → 640m), H4 (next build OOM), H7 (secret fetch retry)~~ — **v1.5.3에서 fix** (DEPLOY_STAMP build arg → image LABEL / disk-cleanup-setup.sh unit 변경 시만 reload / backend 640m + reservation 320m / `NODE_OPTIONS=--max-old-space-size=1536` / 5x 지수백오프 1+2+4+8+16s)
- ~~8443 mTLS rate limit~~ → 일반 endpoint(80/443)에 nginx `limit_req_zone api_zone 60r/s burst 120` + `auth_zone 10r/s burst 20` 적용(v1.5.3 Infra H8). 8443 mTLS 자체는 telemetry SG terraform 작업 별도(여전히 deferred)
- BE H1 (event_stats race), H7 (lifespan task cleanup) — H7은 main.py 이미 task `.cancel()` + try/except로 graceful shutdown 확인됨(v1.5.3 BE review). H1은 큰 마이그/lifecycle 변경 (deferred 유지)
- RDS CMK (운영 자체 액션 — kms_key_id 변경은 RDS 재생성 필요), CSP unsafe-inline 제거 (이전 deferred 유지)
- Dockerfile base image SHA digest 고정 (M2), CloudWatch log retention (M3), /healthz 외부 모니터링 — Phase 9

---

### v1.5.x — 잔존 deferred + reverse geocode + onboarding 모바일 전용 (2026-05-21)

> v1.5.0 이후 같은 날 연속 fix/feat. **alembic head 0030 → 0031 → 0032**. 색상 모드 5종→7종.

**v1.5.0 → v1.5.1 (alembic 0031): 잔존 deferred 12건 일괄**
- Tesla H2/H3: `tesla_signals.ALIASES`에 `IsClimateOn→HvacACEnabled` / `IsPreconditioning→PreconditioningEnabled` 명시. `KEY_TO_COLUMN`에 `PreconditioningEnabled` (광의) 추가.
- Tesla H5: `backend/scripts/register_partner_account.py` — partner token 발급 + `POST /api/1/partner_accounts` + verify (3단계 idempotent). 신규 환경/도메인 변경 시 1회 실행.
- **BE H6 (Alembic 0031)**: `vehicles.customer_id` FK `ON DELETE SET NULL → RESTRICT`. endpoint 가드(vehicles 0건일 때만 customer DELETE)와 DB 가드를 동일 의미로 강화 — 직접 SQL DELETE에서 silent로 차량 N대 NULL되는 위험 차단.
- BE M1: `refill-latest-snapshot`의 dynamic SQL 컬럼명 모델 정의 화이트리스트(`_TELEMETRY_MODEL_COLUMNS`) — 스키마 drift/DDL injection 가드.
- BE M2: `GET /vehicles`의 `data_source=simulated + include_simulated=false` 모순 → 400 reject(이전: silent 빈 결과).
- Infra H4: disk prune 윈도 168h(7d) → 48h. 잦은 deploy(시간당 4~9회) × 7일 누적 EBS 30GB 위협 차단.
- FE H3: `dvTip` leak guard — `showDataTable`/`selectedTs`/`carryForward` 변경 시 stale tip 강제 clear + Esc key.
- FE H4: customers `Dialog` busy 중 backdrop/Esc close 차단 (`onPointerDownOutside`/`onEscapeKeyDown` preventDefault).
- FE H5: `chartDefs` `useMemo` deps에 `t` 추가 + ESLint disable 제거.
- FE H6: `eventTimes` 변경 시 `lastSelectedTsRef` 즉시 동기 갱신 — chip 빠른 클릭 race 차단.
- Onboarding H-5: desktop 사용자가 Step1 pairing deeplink 누르면 안내 Dialog(URL copy + 3단계 가이드). mobile은 그대로.
- Onboarding H-6: "이미 페어링됨" Skip 시 명시 confirm Dialog.
- Onboarding H-8: OnboardVehicleList error catch가 JSON `{detail}` 우선 파싱 — raw JSON 사용자 노출 차단.

**Onboarding 모바일 전용 (MobileGate)**
- `components/MobileGate.tsx` 신규 — UA(`android|iphone|ipad|...`) + `touchstart` + `maxTouchPoints` 감지로 desktop 차단. SSR 첫 render는 children 통과(hydration 안전).
- `/onboard`, `/onboard/vehicles` 둘 다 `<MobileGate>`로 wrap.
- 차단 화면: 아이콘 + 제목 + URL copy + 3단계 가이드(휴대폰 전송 → 휴대폰 브라우저로 → 페어링 시 Tesla 앱 자동 실행).
- 한계: client-side 가드 — 일반 사용자엔 충분, 우회는 가능. 강제 차단 필요 시 nginx UA 차단 또는 backend referer 검증 별도 작업.

**색상 모드 7종 (v1.5.0 → 5종 → v1.5.x 추가 2종 → 총 7종)**
- 기존: light / dark
- 추가 3종 (v1.5.0): **High Contrast** (WCAG AAA), **Sepia** (장시간 가독성), **Solarized Dark**
- 추가 2종 (v1.5.x): **Nord** (차분한 청록), **OLED True Black** (순흑 배경, OLED 절전)
- `globals.css` `@custom-variant` + `:root` / `.dark` / `.hc` / `.sepia` / `.solarized` / `.nord` / `.oled` 단일 mode class
- `lib/theme.ts` `ALL_THEMES = ["light","dark","hc","sepia","solarized","nord","oled"]`
- `components/ThemeToggle.tsx` Popover dropdown — 5 옵션 radio + 아이콘 + 3색 swatch
- FOUC inline script(`layout.tsx`)가 7 모드 모두 인식

**i18n 한국어/영어 어색 표현 일괄 교정**
- ko H 17건: 조사 오류 6건("을 입력하세요" → "다음을 정확히 입력하세요: '{token}'"), Soc → SoC, 최신 → 최근, 발사 → 전송, "OAuth 통과" → "OAuth 인증 완료", VIN 강제 → VIN 형식, 충전 포트 → 충전 포트 열림, 이상 주행 거리 → 이상적 주행거리 등.
- en H 11건: Re-login → Sign in again, "maximum 3" → "maximum of 3", "Cannot be undone" → "This cannot be undone", "Open the button" → "Open the link", "Charge port open" → "Charge port", "Audience" → "Scope", "Letter-start" → "Must start with a letter", "temp set" → "setpoint".
- M 20+건: 이전 소속 → 다른 고객사 소속, produce → 발행, skip → 건너뜀, cooldown → 쿨다운, "차량 당" → "차량당", 미상 → 알 수 없음, "sim run" → "시뮬레이션", 컬럼 헤더 한영 통일.

**v1.5.1 → v1.5.x (alembic 0032): reverse geocoding**

신규 endpoint (옵션):
- `GET /.well-known/appspecific/com.tesla.3p.public-key.pem` — partner_accounts 등록 시 Tesla가 fetch. env `TESLA_PARTNER_PUBLIC_KEY_B64`(또는 `_PEM`) 미설정이면 404 + 안내 메시지. Secrets Manager 자동 fetch.
- `GET /api/v1/geocode/reverse?lat=&lng=&lang=ko|en` — server-side Google Geocoding API + `reverse_geocodes` DB 캐시 (Alembic 0032). ok/zero_results만 캐시, api_error/disabled는 매번 재시도 + UPSERT.

**Frontend reverse geocoding (client-side 채택)**
- `lib/api.ts` `fetchReverseGeocode(lat, lng, lang)` — browser에서 `https://maps.googleapis.com/maps/api/geocode/json` 직접 호출. `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` 사용(기존 Maps JS와 동일 키 + HTTP referrer 제한 보호).
- sessionStorage 캐시 — `(lat_5digit, lng_5digit, lang)` 키 + 500개 LRU. 옛 v1 캐시는 prefix bump로 자동 무시(v2).
- 주소 표시 — 시·도·구·동 수준만, **국가 제외** (사용자 요청).
- 응답 status별 카드/패널 분기 표시(amber 톤):
  - `ok` → 주소
  - `zero_results` → "주소 결과 없음"
  - `disabled` → "주소 기능 비활성 (API 키 미설정)"
  - `api_error` → "주소 조회 실패 (Geocoding API 미활성)"
  - network error → "주소 조회 네트워크 오류"
- `VehicleSummaryPanel` 위치 Section + `FleetVehicleList` 카드 안 MapPin 아이콘 + 주소.

**list_vehicles lat/lng fallback**
- `latest_telemetry`에 lat/lng가 없는 차량은 `telemetry_events DISTINCT ON(vehicle_id) ORDER BY timestamp DESC`로 1 SQL 일괄 fallback. `carry_forward_backfill_all(only_missing=True)`이 미처리한 잔존 케이스 해소.

**고객사 등록 화면 빈 상태**
- `customers.selectFromLeftHint` 신규 키 — "왼쪽 목록에서 고객사를 선택하면 상세 정보가 표시됩니다" (이전: `vehiclesPage.selectHint` 재사용으로 "왼쪽 목록에서 차량을 선택" 부적절 표시).

**알려진 deferred / 운영자 액션 필요**
- **Google Cloud Console에서 Geocoding API enable** 필요(현재 라이브: API key는 있으나 Geocoding API 미활성 → 좌표 보유 차량 카드에 amber "주소 조회 실패" 표시). enable 후 새로고침 1회로 자동 회복.
- **Secrets Manager에 `tesla-partner-public-key.pem` 등록** (옵션) — 등록 시 `/.well-known/...` 자동 serve. 자세한 절차는 `docs/AWS_SETUP_GUIDE_BEGINNER.md` §9.5 / §9.5.1.

---

### v1.4.0 (2026-05-20, `f5b4034`, 태그 v1.4.0) — alembic head **0029**

> **100회 검토 종합 fix(CR/H 9건)** — 4 agent(FE/BE/Infra/Tesla API) deep dive.
> **BE CR1**: `handle_telemetry`가 carry-forward 값을 telemetry_events row에 INSERT하던 버그(history 오염·테이블 부하 폭증) — row 원본 sparse + snapshot 분리.
> **BE CR2**: SELECT prev → UPDATE merged race를 PG `jsonb ||` atomic UPDATE + ts 가드 DB level.
> **Tesla H1**: KEY_TO_COLUMN 매핑이 proto3 Field enum과 불일치(실차량 invalid) — Power→ACChargingPower/DCChargingPower, IsClimateOn→HvacACEnabled, IsPreconditioning→DefrostForPreconditioning, TpmsHardWarning×4→TpmsHardWarnings 단일 비트, UsableBatteryLevel/ChargerActualCurrent/VehicleState/BatteryRange 매핑 제거.
> **Tesla H2**: pairing URL `www.tesla.com → tesla.com` (vehicle-command/fleet-telemetry 공식).
> **FE H1**: `GET /vehicles` 응답에 `latest_telemetry` JSONB inline → 메인 현황 N+1 제거(단일 fetch).
> **FE H4**: VehicleDashboard chip·date range `router.push → router.replace`.
> **Infra C1**: alembic을 Dockerfile CMD에서 분리, `deploy.sh`가 compose up 이전 one-shot 실행. backend healthcheck `start_period 30s→20s`. 무거운 마이그도 라이브 영향 0.
> **응답 스키마**: `VehicleListItem.latest_telemetry: dict | null` 추가.

### v1.2.0 (2026-05-19, `ee23d14`, 태그 v1.2.0) — alembic head **0025** (신규 endpoint 1: `/route`)

> **frontend-only·API/스키마/인프라 계약 불변**(breaking 아님 → minor). v1.1.0 이후 68커밋: Next→Vite 마이그·전 UI 흑백 재작성·Tailwind v4·shadcn 전면(프리미티브 16종)·차트 recharts→chart.js·지도 OSM→Google Maps·테마 토글·달력/폼컨트롤 shadcn. 품질: 20회 검토 ×5 + 100회 검토 ×1(FE/BE/인프라) — 누적 회귀 0, BE 무변·계약 1:1 일치·보안 안전. 100회 검토 fix: H1(`main.tf` IAM ARN git 커밋 — terraform apply는 됐으나 IaC 코드 누락분 동기화)·FE-L2(TelemetrySettingsForm Stat highlight 삼항 반대 swap). 상세: `memory/ui_blackwhite_migration.md`. 아래는 그 누적 항목.
- **프론트엔드 스택 전환: Next.js App Router → Vite + react-router-dom SPA (frontend-only, cutover `573c8a5`)** — **API·스키마·alembic·백엔드 일체 불변**(동일 `/api/v1` 계약). 사용자 결정(내부 어드민 → SSR 불요). app/ 파일라우팅 7페이지 → `src/router.tsx`(createBrowserRouter)+`src/routes/*`, RSC/`getServerT` → 클라이언트+`useI18n`(쿠키 단일출처, `lib/i18n/server.ts` 폐기), `next/link`·`next/navigation` → react-router, `src/middleware.ts` host 라우팅 → `docker/nginx.conf` map+if 이관, frontend 컨테이너 Next standalone → **nginx 정적 dist 서빙**(:3000). 빌드 `tsc --noEmit && vite build`, `npm ci`+검증된 `frontend/package-lock.json`, `deploy.sh` 추출 전 frontend/backend clean. 전환 중 deploy 파이프라인 잠재결함 3건(게이트 nginx-t false-fail / stale lock+`npm install` 미강제 / **deploy.sh dirty extraction**)으로 2회 S2 outage·즉시 복구(`compose up -d --no-build`) — 마이그 코드는 매 게이트 `tsc+vite ✓`로 처음부터 건전. 상세: `docs/INCIDENT_2026-05-19_vite_cutover.md`, `teslafleet_lessons.md` ## 43. 라이브 검증: 7라우트 200+딥링크 SPA fallback, `/assets/` Vite·`_next` 0, onboard 308 host격리.
- **Alembic 0025 — 기본 텔레메트리 config에 `LifetimeEnergyUsed` 추가**: 대시보드 "누적 에너지 사용 추이"(컬럼 `lifetime_energy_used_kwh`) 차트는 신호 `LifetimeEnergyUsed`로 채워지는데 기본 시드 config(0007+0010)에 없어 **default 모드 시뮬레이터가 미emit → 시뮬 차량 차트 빈 화면**(rich 모드는 `RICH_SIGNAL_CATALOG`에 포함되어 정상). 0025가 1행 추가(`interval_seconds=60`, `enabled=true` 명시, `ON CONFLICT (signal_name) DO NOTHING` 멱등, downgrade는 0010식 `ALEMBIC_ALLOW_DESTRUCTIVE_DOWNGRADE` 가드). **코드·API 표면·스키마 불변** — generator/parser/컬럼/프론트 차트/known-signals 모두 기존 존재, 마이그 1행이 전부. 실차량도 이제 기본 스트림에 포함(admin UI에서 `enabled=false`로 제외 가능). 라이브 검증: alembic head=0025, `GET /settings/telemetry-config`에 `LifetimeEnergyUsed enabled=true`, 기존 sim 차량 default 모드 run → `lifetime_energy_used_kwh` non-null + 누적 추이 차트 렌더
- **UI 표기 통일성 정비 (frontend-only, `71ca915`+`b367c69`)** — API·스키마·alembic 불변(head 0025 유지): 사용자 보고("시뮬 최근이력 시각 `7h 0분`/`10분 3s` 언어 혼용") → 서브에이전트 frontend 전수 감사 후 2단계. **P1**: duration 단위 언어혼용·하드코딩 영문 라벨·dict `ko` 값이 영문이던 항목(`alerts on`→`알림 켜짐` 등)·하드코딩 `<th>`/`<span>` 일괄 i18n화. **P2**: `lib/format.ts` 신규(순수·RSC 안전) 단일 정본 — 타임스탬프 5종·duration 3종·천단위 3종 정책을 `fmtStamp/fmtClock/fmtDateTime/fmtDay/fmtInt/fmtMoney/fmt{Duration,Elapsed,AlertDuration,ElapsedShort}`로 통합(`common.dur*` 공유). 호출부 *가시 출력* 보존(강제 동일화 X), TelemetryChart는 recharts 전용 포맷터라 의도적 제외. P2 순 사용자 가시 변화 = SeedManager 적재이력 `loaded_at`이 ko/en 토글 반영(기존 no-locale 버그 수정) 1건. **P3**(한 건씩 안전 처리, `6907faf`/`0d996a9`/`8b82c0d`/`119ea08`/`a6d903c`): 실수정 5 — #7 SEED 배지 i18n(가시0), #5 audiences 구분자 `/`→`, `, #6 공유 `LoadingPlaceholder`, #4 액션버튼 선행 글리프 ▶■↻ 제거(의미마커 ⚠/✓ 유지), #3 최상위 `<section>` 패딩 `p-3 sm:p-6` 통일(사용자 승인) — + false-positive 2 미변경: #1 status→색 3맵은 서로 다른 도메인/UI요소라 비중복, #2 VehicleDashboard 내부 sticky는 컨트롤 오버레이라 의도적 상이(정렬 시 z-fighting). 전부 게이트 통과·라이브 검증, API·스키마·alembic(0025) 불변.
- **전체 UI 100x 검토 잔여 remediation (frontend-only, `ec91ae1`/`a1ba742`/`41c9e47`/`506472c`)** — API·스키마·alembic 불변(head 0025): 3 서브에이전트(시각·i18n/a11y·상태/회귀) 전수 감사 → 위험분리 4배포(전부 게이트통과·라이브검증). **B1**: `/onboard` `min-h-screen`→`min-h-full`(layout `<main>` 스크롤컨테이너라 항상 overflow하던 CR) · `red-*`→`rose-*` 팔레트 · `fmtAlertDuration` NaN/음수 가드 · rich 신호 stale 카운트 3곳→58 · `String(e)`→`e.message` ×4. **B2(a11y)**: AlertsTimeline·VehicleDashboard 스크러버 `<div role=button>`에 `tabIndex`+`onKeyDown`(키보드 비조작 CR) · 슬라이더 aria-label 전용키 · progressbar `aria-busy`/`aria-valuetext` · error 배너 `role=alert`. **B3(state)**: SeedManager 파괴(delete)↔적재(ingest) 상호배타(`deleteRunning`/`ingestRunning` 파생가드, 5버튼 disabled 추가만 — delete 폴링 중 타 삭제가 공유 카드 클로버 CR + ingest/delete 겹침 race). **error.tsx**: 하드코딩 양언어→locale별, error boundary 안전 위해 `useI18n`(provider 없으면 throw) 대신 쿠키+exported `translate()` context-비의존. **deferred→해소(`70a6301`, Vite 운영본)**: SeedManager onInsertMonth/onRetryAllFailed 루프 + onDeleteMonth/onDelete while 최상단 + Sim `refresh`/`refreshSummary`의 setState-after-unmount `mountedRef` 가드 적용(additive·UI 무변, 게이트==배포 입증된 첫 정상 배포). FP ~28건은 영구 미변경.
- **전 UI 흑백 전면 재작성 — Tailwind v4 + shadcn/ui + chart.js (frontend-only, B0~B5 `b558d2e`→`9f9732d`)** — **API·스키마·alembic·백엔드 일체 불변**(동일 `/api/v1` 계약). 사용자 결정(AskUserQuestion): 전 UI 전면 재작성 / 흑백 베이스 + 상태색 최소(destructive·success·warning만 절제 1단계, a11y) / 차트 react-chartjs-2. Tailwind v3→v4(`@tailwindcss/vite`·`@import`·`@theme`, postcss/JS config 삭제) + shadcn(components.json·`cn`·zinc 흑백 CSS변수 다크 기본, 프리미티브 9종) + **recharts→chart.js**(`chartjs-plugin-annotation`, 전 기능 보존, 번들 JS 1069→953KB·CSS 87→72KB) + 763 색클래스→0(VehicleSilhouette COLOR_MAP 차량실색만 의도적 예외). 큰 파일(VehicleDashboard 1421·SeedManager 1130·SimulatorControl 709·TelemetrySettingsForm 815)은 Write 금지·Python `re.sub`로 색클래스만 치환 — delete-job 폴링·mountedRef·토큰 confirm·검증배지 분기·타이머 가드 등 정교한 로직 100% 무손상. 6배치 각 게이트 통과·라이브 검증(7라우트 200/308·딥링크 SPA fallback·대시보드·자산해시 일치). 시각·인터랙션 동작은 HTTP 검증 불가 → tsc/게이트/라우트로 보장. lock 재현성(lesson #43). 상세: `memory/ui_blackwhite_migration.md`.
  - **데이터 시각화 색 예외(사용자 요청)**: 차트 6시리즈 원본색 복원(`58b81c9`) + 슬라이더 selected 세로 커서선 보라 `#a855f7` 3곳 복원(`cafece6`) + SectionTimeline 데이터 빈도 막대를 차트 시리즈 색으로(`bebe8d8`, 차트↔타임라인 시각 연결). UI 크롬은 흑백 유지 — **데이터 식별/시각화는 컬러, 크롬은 흑백** 원칙.
  - **OSM(Leaflet)→Google Maps JS API 교체(frontend+infra, `cacdbe5`, 사용자 요청)** — API·스키마 불변. `@vis.gl/react-google-maps`, leaflet 제거(번들 JS 953→825·CSS 72→56KB). VehicleMap/RouteMap 재작성·흑백 다크 styles·mapProvider 토글 제거. **키 인프라**: Secrets Manager `/teslafleet/sphere-dev/google-maps-api-key` → deploy.sh fetch → docker/.env → docker-compose `build.args` → Dockerfile `ARG`/`ENV` → Vite 빌드 인라인(클라 노출 정상 — GCP Console **HTTP 리퍼러 제한 필수**, 운영자 작업). `infra/envs/dev/main.tf` ec2_secrets_read에 신규 secret ARN 추가(6-char suffix 패턴). **⚠ 운영 필수: 신규 secret이라 EC2 IAM에 read 권한 추가 `terraform apply` 선행 필요**(미적용 시 deploy fetch AccessDenied→빈 키→지도 "키 미설정" graceful). plan 검증 완료(0 add/2 change in-place/0 destroy 무중단). 운영 후속: IAM apply(사용자 직접 — 자동분류기 차단) → eventual consistency 지연(try1 DENIED→~30s→try2 OK) → deploy 재실행 → 키 인라인 검증 완료.
  - **지도 후속(`b6426d4`~`6f56e06`, 사용자 요청 연쇄)** — frontend+infra, API 불변. (1) **CSP 함정 fix(`b6426d4`)**: `script-src 'self'`가 `maps.googleapis.com` 동적 script 차단(leaflet은 self 번들이라 무관했음) → `docker/nginx.conf` CSP에 `script-src`·`connect-src`(maps.googleapis/gstatic)·`worker-src blob:`·`img-src blob:` 허용. 외부 script 라이브러리 도입 시 CSP 동반 점검 필수(lesson). (2) 흑백 다크 styles 제거 → **기본 컬러 지도**(`90db8f5`). (3) **단일위치 지도+전체경로 지도 통합(`5d5191c`)**: `VehicleMap.tsx` 삭제, 경로 지도 하나에 전체 경로 polyline + 시작/끝 + **슬라이더 연동 현재 위치 마커**(carryForward, 타임라인 변경 시 이동). (4) **`ROUTE_COLORS` 단일출처(`17722d3`)**: `lib/mapStyle.ts`에서 start녹/end적/current보라/path노랑 — VehicleRouteMap 마커·polyline ↔ VehicleDashboard 범례 동일 참조(범례=실제, 드리프트 불가). 범례 plain text→실제 색 dot JSX, dict `routeLegend`→조각 4키. (5) `routeOpen` 기본 `true`(경로 지도 진입 시 펼침, `6f56e06`).
  - **20회 심층 검토(`6f56e06`, 3에이전트 전수 감사)** — 이번 세션 누적 변경(마이그→흑백→토글/차트/지도/범례)에 대해 **실 데이터 연동·추가 로직 모두 안전, 실 버그 0** 확인. (A 데이터) api.ts/types.ts git 격리+backend 스키마 전수 대조 일치. (C 회귀) re.sub 4대형파일 무손상(JS로직·hook deps 변경 0)·tsc exit 0·theme/i18n 안전. (B 차트지도) chart.js·@vis.gl recharts·Leaflet 기능 등가. **M1 fix**: TelemetryChart tooltip `fields.find(label)`→`fields[datasetIndex]`(recharts dataKey 등가, dual-axis 동일 label 오매칭 잠재위험 차단). **M2 deferred**: data/options useMemo 미적용(실버그 아님 + deps 실수 시 stale 위험 도입).
  - **shadcn 컴포넌트 전면 적용(`821c17f` 배치1 + `1c4225c` 배치2~5, 사용자 결정)** — frontend-only, API·스키마 불변. B0~B4에서 로직 회귀 위험으로 미룬 큰 파일(VehicleDashboard/SimulatorControl/TelemetrySettingsForm/SeedManager/AlertsTimeline) 인라인 `button`/`input` → shadcn `Button`/`Input`/`Slider`/`Textarea`. **`Slider`(@radix-ui/react-slider)·`Textarea` 프리미티브 신규**(B0 9→11종). 로직 100% 보존(폴링·mountedRef·배타가드·타이머·validateSignals·handleStart/Stop/Save/Repush — 1c4225c는 onClick/onChange/disabled/value만 교체). **native 유지**: checkbox/radio/`<select>`(사용자 `button`/`input` 범위 밖 + Radix 회귀 위험), SeedManager `onInsertMonth`(동적 status색 `cls`라 Button variant 충돌 — 인라인 토큰 유지). 부수: TelemetrySettingsForm h2 색버그 인접수정(`text-primary-foreground`→`text-foreground`, 다크서 안 보이던 것). GATE×2·7라우트·딥링크 200. 시각 회귀(버튼/입력 크기·정렬)는 사용자 결정대로 진행, 브라우저 육안 영역.
- **신규 `GET /api/v1/telemetry/vehicles/{vehicle_id}/route`**: 경로 지도 전용. 좌표(lat·lng) 있는 원본 row를 **무샘플링** `{ts,lat,lng}` 시간순 반환(`from`/`to`/`last_days`/`limit` 기본 5만·최대 20만). 스키마 `RoutePointOut` 신규. events 다운샘플로 폴리라인이 도로를 벗어나던 문제 해결 — 조밀 원본 좌표가 도로를 자연히 따라감. 무료·키없음·인프라0(map-matching 엔진 미사용).
  - cap 초과 시 **가장 최근 limit개**(DESC limit→ASC 재정렬, 과거 first-N 아님; 경계 범위는 동일 집합) — `76cccd9`
  - **GPS outlier 필터**(`7162645`/`3debd17`): 직전 채택점 대비 haversine 거리/Δt 속도 >75 m/s(~270km/h)면 제거(채택점 유지로 단일 outlier 왕복 2구간 차단), dt≤0은 1km 초과만, sparse 갭 보존. 3점 합의 시드로 '가장 오래된 점이 outlier'인 cascade 방지. 라이브 검증: 불가능(>75) 구간 0건, dense ~2-3%만 감소
- **Tesla 스트리밍 파서 정합성 수정**(`_extract_value`): Tesla 공식 `Value` oneof 중 누락됐던 **`longValue`·`floatValue`(숫자형) 처리 추가** + 미열거 `*Value` 스칼라(str/int/float/bool) 일반 흡수. 이전엔 longValue/floatValue가 "unknown"→raw_data wrapper 객체로 손실(매핑 컬럼 null). prefer_typed 환경/일부 typed 필드 신호가 이제 정상 추출. 응답 스키마 불변(어떤 신호가 컬럼/스칼라로 잡히는지 정확도 개선)
- **`fleet_telemetry_config`에 `prefer_typed: true` 추가**: Tesla 권장(신규 연동) — 숫자·enum을 stringValue 대신 본래 typed oneof로 전송(모호성 제거·정밀도 보존). 위 파서 수정으로 전 typed 형식 견고 처리됨. **실 Tesla-페어링 차량의 신규 스트림에만 영향**(시뮬·seeded 무관). 현재 실 live 차량 0대 → 코드 적용·파서 end-to-end 검증 완료, 실차량 staged rollout(`POST /onboard/register/{vin}` 1대 선검증 → 전체)은 실 owner 연결 시 운영 절차. 스키마·API 표면 불변, alembic 0024
- **100x FE/BE/Infra 검토 정합성 수정** (`4d13e1f`, 핫픽스 `3f988c7`) — 스키마·API 표면·alembic(0024) 불변, 값/동작 정확도만 개선:
  - **월 집계 UTC 일치**(H-2): DB 세션 timezone을 UTC 고정 → `GET /admin/seed/event-stats`·`/admin/seed/monthly-overview`의 `extract(year/month, …)` 월 버킷이 UTC-bound `DELETE /admin/seed/events`와 일치. 이전엔 세션 TZ가 UTC 아닐 시 "월 삭제 후 잔존 row 표시" 가능. 라이브 검증: event-stats 정상, DB 연결 무영향
  - **좌표 위생 처리**(H-5): 스트리밍 `locationValue` lat/lng를 finite + 지리범위(±90/±180) 검증 후에만 저장 → `/telemetry/.../route`·`latest`·`events`에 NaN/Inf/범위초과 GPS 오류 미유입(이전엔 raw 저장 + 경로필터 NaN 비교 우회)
  - **시크릿 fetch 실패 loud**(CR-1): `DATABASE_URL_SECRET_ID` 설정 시 Secrets Manager 조회 실패하면 localhost dev fallback 대신 즉시 RuntimeError(운영 오접속 차단) — 부팅 동작 변화, API 표면 무관
  - frontend: 상태 카드가 carry-forward 값 표시(이전 sparse raw → 대부분 '—'), 데이터보기/차트 perf, SeedManager 삭제 polling 언마운트 안전. Infra: `deploy.sh`가 nginx 재시작 내재화
- **`GET /vehicles` 응답 신선도 수정** (`165f78e`): `event_count`/`earliest_timestamp`/`latest_timestamp`가 이제 write 시점에 실시간 정확(이전엔 resync까지 최대 24h stale). 응답 스키마·필드명 불변 — 값의 최신성만 개선. 라이브/시뮬은 `handle_telemetry`, 적재는 `_ingest_one_dump`가 INSERT와 같은 트랜잭션에서 비정규화 컬럼 증분 유지. delete 후 일시 과대는 daily `resync_vehicle_stats`가 보정
- `/vehicles/{id}` 대시보드 **해당 시점 데이터 보기** 표: 항목명 검색 + '측정된 항목만' 토글 + 전용 컬럼/원본(raw_data) 2섹션 분리 (frontend)
- 행 hover **항목 설명 툴팁** (`frontend/src/lib/signalInfo.ts`: Tesla 256 신호 + 정규화 64 컬럼 전수, ko/en, 미등록은 이름 추정). native `title` → `position:fixed` 커스텀 패널(설명+전체값) (frontend)

### v1.0.3 (`3cd7395`, 2026-05-15) — alembic head 0022
- `GET /telemetry/.../events` 다운샘플 **row-sampling → column-aware time-bucket** (PostgreSQL) + SQLite fallback. sparse 신호 보존(energy_remaining 13→295점). `raw_data`는 bucket path에서 `null`. **60초 TTL 캐시** (cold ~9s / warm ~0.3s)
- **설정 신호검증 3종** (Alembic 0021): `GET /settings/known-signals` 신규(Tesla 256 신호+alias) / `GET /settings/telemetry-config` 응답에 `last_validation_{status,at,error}` / `POST /settings/repush-all`·`POST /onboard/register` 응답에 `invalid_signals[]`
- **삭제 async job** (Alembic 0022): `DELETE /admin/seed/events`·`/vehicles/{id}` → 0건 동기 / 비-0건 `202 started`+`job_id`. `GET /admin/seed/delete-jobs/{job_id}` 신규 polling. `sim_delete_events`에 `status`/`finished_at`/`error`. 409=in_progress 중복(stale>1h 자가복구)
- `POST /admin/seed/scan-s3` **제거** (dumps/ 미사용)
- frontend: 에너지 차트 누적/잔여 분리, sparse 측정점 dot+배지, overview Status/Action 통합

### v1.0.2 (2026-05-14) — alembic head 0020
- Seed 관리 **+7 endpoint** (Alembic 0019/0020): `DELETE /admin/seed/vehicles/{id}`·`/events`, `POST /admin/seed/ingest-one`, `GET /admin/seed/{monthly-overview,list-month-files,imports}`
- `SimRunCreate.interval_seconds_override` 필드 (빈도 UX)
- 에러 표에 412/429/502 추가

### v1.0.0 (`86cf52f`, 2026-05-14)
- 최초 작성 — 24 endpoint
