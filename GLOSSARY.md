# TeslaFleet 기술 용어집 (Glossary)

> **이 문서는 누구를 위한 것인가요?** 프로그래밍·클라우드가 처음이거나 이 프로젝트에 막 합류한 분이 코드·다른 문서를 읽다 모르는 용어를 만났을 때 찾아보는 사전입니다. 각 용어는 **① 한 줄 쉬운 정의 → ② 풀어쓴 설명(비유) → ③ 이 프로젝트에서의 쓰임** 순서로 설명합니다.

> 네 개의 큰 꼭지로 나뉩니다 — **FrontEnd**(화면) · **BackEnd**(서버) · **인프라**(클라우드) · **데이터**(파이프라인). 처음 본다면 위에서부터 천천히 읽으면 전체 그림이 그려집니다. (다른 문서: 전체 구조는 `ARCHITECTURE.md`, API는 `API_REFERENCE.md`, DB는 `DB_SCHEMA.md`.)

## 목차

- [🖥️ FrontEnd — 사용자가 보는 화면](#frontend--사용자가-보는-화면)
  - [웹 앱 구조 — 사용자가 보는 화면이 어떻게 만들어지는가](#웹-앱-구조--사용자가-보는-화면이-어떻게-만들어지는가)
  - [데이터 흐름 — 화면이 서버에서 정보를 가져와 그리는 과정](#데이터-흐름--화면이-서버에서-정보를-가져와-그리는-과정)
  - [성능 최적화 — 화면을 빠르게 로드하고 부드럽게 조작하기](#성능-최적화--화면을-빠르게-로드하고-부드럽게-조작하기)
  - [빌드 및 배포 — 코드를 테스트하고 실제 사용자에게 배포](#빌드-및-배포--코드를-테스트하고-실제-사용자에게-배포)
  - [UI 컴포넌트 라이브러리 — 버튼, 입력칸, 드롭다운 등을 빠르고 일관되게 만들기](#ui-컴포넌트-라이브러리--버튼-입력칸-드롭다운-등을-빠르고-일관되게-만들기)
  - [실시간 데이터 및 통신 — 차량의 위치·배터리 상태를 계속 업데이트](#실시간-데이터-및-통신--차량의-위치배터리-상태를-계속-업데이트)
- [⚙️ BackEnd — 화면 뒤에서 일하는 서버](#backend--화면-뒤에서-일하는-서버)
  - [웹 요청 - API 계층](#웹-요청---api-계층)
  - [인증 & 권한 체크](#인증--권한-체크)
  - [데이터 모델링 & ORM](#데이터-모델링--orm)
  - [데이터 적재 & 처리 흐름](#데이터-적재--처리-흐름)
  - [조회 & 캐싱 최적화](#조회--캐싱-최적화)
  - [백그라운드 작업 & 스케줄링](#백그라운드-작업--스케줄링)
- [☁️ 인프라 — 서비스가 돌아가는 클라우드 토대](#인프라--서비스가-돌아가는-클라우드-토대)
  - [클라우드 기초 개념](#클라우드-기초-개념)
  - [컴퓨팅 및 서버 (계산·처리)](#컴퓨팅-및-서버-계산처리)
  - [데이터 저장 및 관리](#데이터-저장-및-관리)
  - [메시징 및 데이터 흐름 (파이프라인)](#메시징-및-데이터-흐름-파이프라인)
  - [데이터 처리 및 변환 (ETL/분석)](#데이터-처리-및-변환-etl분석)
  - [보안 및 비밀 관리](#보안-및-비밀-관리)
  - [컨테이너 및 배포](#컨테이너-및-배포)
  - [모니터링 및 운영](#모니터링-및-운영)
- [📊 데이터 — 차량 신호가 흘러 분석되는 길](#데이터--차량-신호가-흘러-분석되는-길)
  - [1. 데이터 수집 — 차량이 보내는 신호가 모이는 길](#1-데이터-수집--차량이-보내는-신호가-모이는-길)
  - [2. 실시간 서빙 경로 — 대시보드에 '지금 상태'를 보여주기](#2-실시간-서빙-경로--대시보드에-지금-상태를-보여주기)
  - [3. 데이터 저장소 — 분석을 위한 '물고기 양식장' 아키텍처](#3-데이터-저장소--분석을-위한-물고기-양식장-아키텍처)
  - [4. 데이터 검증 — 나쁜 데이터 걸러내기](#4-데이터-검증--나쁜-데이터-걸러내기)
  - [5. 데이터 흐름 최적화 — 효율·신뢰·안전](#5-데이터-흐름-최적화--효율신뢰안전)
  - [6. 운영 · 모니터링 — 시스템이 잘 작동하는지 확인하기](#6-운영--모니터링--시스템이-잘-작동하는지-확인하기)
  - [7. 데이터 전송·인코딩 — 차량이 안전하게 보내는 방식](#7-데이터-전송인코딩--차량이-안전하게-보내는-방식)


---

## 🖥️ FrontEnd — 사용자가 보는 화면

> 브라우저에서 보이는 화면(지도·차트·표·버튼)을 만들고, 백엔드에서 데이터를 받아 그리는 부분입니다.

### 웹 앱 구조 — 사용자가 보는 화면이 어떻게 만들어지는가

_TeslaFleet은 Next.js(구글 맵, 차트를 빠르게 로드하는 웹 프레임워크)로 만들어졌으며, 로그인부터 대시보드까지 어떻게 작동하는지 이해하는 것이 핵심입니다._

**Next.js / React**
  
› _구글 지도, 차트 등을 빠르게 보여주는 웹 화면 제작 도구_
  
Next.js는 구글이 아닌 Vercel이 만든 웹앱 틀로, React라는 부품 조립 방식을 사용합니다. TeslaFleet은 static export라는 방식으로 빌드되어, 서버가 없이도 순수 HTML/JS로 모든 화면을 보여줍니다. 사용자가 대시보드에 접근하면 먼저 로그인 페이지가 뜨고, 인증된 후 지도·차트·표 같은 부품들이 화면에 '그려지는' 과정입니다. 이 프로젝트에서는 Google Maps(차량 위치 표시), Chart.js(시계열 차트), Tailwind CSS(스타일)가 조합되어 작동합니다.

**App Router (Next.js 15)**
  
› _주소창의 경로(/vehicles, /admin 등)에 따라 어떤 화면을 보여줄지 정하는 시스템_
  
사용자가 브라우저의 주소창에 `https://fleet.example.com/vehicles`라고 입력하면, Next.js의 App Router가 `/vehicles` 경로에 맞는 React 컴포넌트를 찾아 화면을 그립니다. 이 프로젝트는 /login (로그인), /onboard (차주 페어링), /vehicles (차량 목록), /admin/* (관리자 메뉴) 같은 여러 경로를 가집니다. App Router는 폴더 구조(`/src/app/vehicles/`)로 경로를 자동 정의하는 '파일 기반 라우팅'을 합니다.

**Static Export / SPA(Single Page App)**
  
› _서버 없이 순수 HTML/JS만으로 모든 것을 처리하는 앱 방식_
  
`next build`를 실행하면 TeslaFleet은 `/out` 폴더에 정적 HTML 파일들을 만듭니다. 이 파일들을 nginx 같은 웹 서버에 올리기만 하면 별도 Node.js 서버가 필요 없습니다. 사용자가 페이지를 이동할 때 브라우저는 매번 서버에 요청하지 않고, 이미 받은 JS(약 700KB)를 실행해서 새 화면을 그립니다(매우 빠름). 대신 데이터는 백엔드 API(`/api/v1/...`)를 호출해서 동적으로 가져옵니다. 이를 SPA라고 부르며, React가 마크업을 동적으로 생성하고 상태를 메모리에 관리합니다.

**Component / Props (React)**
  
› _화면을 조립하는 재사용 가능한 부품 — 부품이 필요한 정보를 '입력값'으로 받음_
  
React의 핵심은 화면을 여러 부품으로 나누어 관리하는 것입니다. 예를 들어 '차량 카드' 컴포넌트는 차량 이름, 배터리 백분율, 위도/경도 같은 정보를 prop(입력값)으로 받아서, 그 정보를 예쁘게 그려냅니다. 같은 부품을 여러 곳에 재사용할 수 있습니다. TeslaFleet의 `FleetVehicleList` 컴포넌트는 `vehicles` 배열을 받아 각 차량을 카드로 표시하고, `VehicleSummaryPanel` 컴포넌트는 선택된 차량의 상세 정보를 보여줍니다. 부품 간에 정보를 전달할 때는 항상 위에서 아래로만(부모→자식) prop으로 전달합니다.

**State / setState (React)**
  
› _화면의 '현재 상태'를 메모리에 저장하고, 변경되면 화면을 다시 그리도록 하는 메커니즘_
  
사용자가 '고객사 필터'를 선택하면, 그 선택값을 state라는 메모리 변수에 저장합니다. State가 바뀌면 React는 자동으로 '화면을 다시 그려야 한다'고 알아차리고, 새로운 state 값으로 컴포넌트를 재렌더링합니다. 예: `const [selectedVid, setSelectedVid] = useState<string | null>(null)` — `selectedVid`는 현재 선택된 차량 ID, `setSelectedVid(newId)`로 그 값을 바꾸면 화면이 자동으로 업데이트됩니다. 이것이 '반응형'이라는 뜻입니다. State를 prop으로 자식에게 전달하고, 자식에서 변경하고 싶으면 setState 함수를 함께 내려줍니다.

**Hook (React)**
  
› _React 함수형 컴포넌트 내에서 state·effect·context 등을 '갈고리처럼' 끌어와 쓰는 함수들_
  
React Hook은 모두 `use`로 시작합니다. `useState` — state와 setState를 만들기, `useEffect` — 화면 그려진 후 데이터 로드 등 작업 실행, `useCallback` — 함수를 메모리에 고정해 자식 props 변경 방지, `useMemo` — 복잡한 계산 결과를 캐시해 성능 향상, `useContext` — 전역 정보(로그인 상태, 언어 설정) 가져오기. TeslaFleet은 `useVehicleDetailData` 커스텀 훅을 만들어 차량 상세 데이터를 한 곳에서 로드하고, 모든 페이지가 그것을 재사용합니다.

**useEffect (데이터 로드 시점)**
  
› _화면이 그려진 직후, 또는 특정 값이 바뀐 직후에 '한 번만' 데이터를 가져오는 방식_
  
`useEffect(() => { 데이터 로드 }, [의존값])` — 대괄호 안의 '의존값'이 바뀔 때만 내부 코드를 실행합니다. 예를 들어 차량 ID가 바뀌면(`[id]`), 그 차량의 데이터를 새로 가져옵니다. 빈 배열 `[]`이면 컴포넌트가 처음 마운트될 때 딱 한 번만 실행(예: 고객사 목록 조회). 의존값이 없으면 매번 렌더링할 때마다 실행되어 무한 루프에 빠집니다(버그). TeslaFleet의 page.tsx에서 `useEffect(() => { fetchVehicles(...) }, [includeSim, customerId])`는 시뮬 토글이나 고객사 필터가 바뀔 때마다 차량 목록을 새로 로드합니다.

**useMemo / useCallback (성능 최적화)**
  
› _같은 계산/함수를 매번 새로 하지 말고 '저장된 결과'를 재사용해 화면 깜빡임을 줄이기_
  
`useMemo(() => 복잡한계산(), [의존값])`은 의존값이 바뀌지 않으면 이전 계산 결과를 다시 쓰고, `useCallback(() => { 함수내용 }, [의존값])`은 함수 객체 자체를 메모리에 고정합니다. 자식 컴포넌트에 함수를 prop으로 내릴 때, 매번 새로운 함수 객체를 만들면 자식이 '부모가 변했나'라고 착각해 불필요하게 재렌더링됩니다. 저장하면 자식이 '아, 같은 함수다'라고 알아차려 재렌더링을 스킵합니다. 예: 마커 배열을 `useMemo`로 저장하면, 지도 재렌더링 시 마커 위치 계산을 다시 하지 않습니다.

**Suspense (비동기 렌더링)**
  
› _데이터가 도착할 때까지 '로딩 상태'를 보여주고, 도착하면 콘텐츠로 바꾸기_
  
`<Suspense fallback={<로딩UI>}><콘텐츠/></Suspense>`는 콘텐츠가 데이터를 기다리는 동안 fallback UI를 보여줍니다. TeslaFleet의 메인 페이지는 `<Suspense fallback={null}><FleetInner /></Suspense>`로 감싸서, 첫 렌더링이 즉시 일어나고 배경이 빈 채로 잠깐 보인 후 지도/차량 목록이 점진적으로 로드됩니다. modern React(v18+)와 함께 쓰면 서버-클라이언트 스트리밍 렌더링도 가능하지만, TeslaFleet은 static export라서 '클라이언트가 JS를 실행하기 전까지 대기'하는 용도로만 사용합니다.

### 데이터 흐름 — 화면이 서버에서 정보를 가져와 그리는 과정

_TeslaFleet의 모든 정보(차량 위치, 배터리 상태, 이벤트 로그)는 백엔드 API에서 옵니다. 프론트엔드는 API를 호출하고, 받은 JSON 데이터를 화면에 그립니다._

**API(Application Programming Interface) / fetch**
  
› _프론트엔드가 백엔드 서버에 '특정 데이터를 달라'고 요청하는 방법_
  
모든 웹앱은 화면에 보여줄 정보를 서버에서 가져옵니다. TeslaFleet은 `/api/v1/vehicles` (차량 목록), `/api/v1/telemetry/vehicles/{id}/events` (차량의 텔레메트리 이벤트), `/api/v1/telemetry/vehicles/{id}/latest` (차량의 최신 위치·carry-forward 머지) 같은 경로로 RESTful API를 호출합니다. JavaScript의 `fetch()` 함수가 HTTP 요청을 보내고, 서버가 JSON 형식 응답을 줍니다. TeslaFleet의 `api.ts` 파일이 모든 API 호출을 중앙에서 관리합니다 (`fetchVehicles`, `fetchTelemetryEvents`, `fetchLatestTelemetry` 등). 요청할 때 HttpOnly 쿠키(`__Host-tf_account`)로 인증을 전달하고, 응답이 401(인증 실패)이면 창에 'tf:unauthorized' 이벤트를 쏴서 AuthProvider에 알립니다.

**JSON (JavaScript Object Notation)**
  
› _데이터를 문자열로 표현하는 규칙 — 배열과 객체로 구조화_
  
서버가 보내는 데이터는 JSON 형식입니다. 예: `{ "id": "tesla-001", "display_name": "Model 3 #1", "latitude": 37.5, "longitude": 127.0 }`. 객체는 `{}`로 감싸고 키-값을 `: `로 연결합니다. 배열은 `[]`로 감싸고 쉼표로 분리합니다(예: `[{차량1}, {차량2}]`). `null`, `true/false`, 숫자, 문자열을 값으로 가질 수 있습니다. TypeScript는 이 JSON을 `Vehicle`, `TelemetryEvent` 같은 '타입'으로 변환해서, 실수를 미리 잡습니다(잘못된 필드명을 쓰면 컴파일 에러).

**TypeScript / Type Definition**
  
› _JavaScript에 '강한 타입 체크'를 더한 언어 — 실수를 컴파일 단계에서 잡기_
  
순수 JavaScript는 변수 타입이 자유로워서 `const x = "hello"; x.toUpperCase()` (문자열 메서드)와 `const x = 123; x.toUpperCase()` (숫자에 메서드 호출 = 에러)를 구별 못 합니다. TypeScript는 각 변수·함수 인자·함수 반환값에 '타입'을 명시해서, 컴파일 시점에 에러를 검출합니다. TeslaFleet의 `/lib/types.ts`에서 `interface Vehicle { id: string; vin: string; ... }`로 정의하면, 코드에서 `vehicle.id`는 반드시 문자열이어야 하고, `vehicle.invalid_field`라고 쓰면 '그런 필드는 없다'고 에러를 냅니다. 이를 '타입 안전성'이라 부르며, 버그를 줄여줍니다. TeslaFleet은 매우 강한 타입 설정(`"strict": true`)을 사용합니다.

**useVehicleDetailData (커스텀 훅 / 점진 로드)**
  
› _차량 상세 페이지가 필요한 모든 데이터(차량 정보, 이벤트, 알림)를 한 곳에서 로드하고 관리_
  
차량 상세 페이지(`/vehicles/[id]`)와 split view(메인 페이지에서 차량 선택)는 같은 데이터를 필요로 합니다. 이전엔 두 페이지에 중복 코드가 있었으나, 버그 위험 때문에 단일 훅으로 통합했습니다. `useVehicleDetailData(id, from, to, lastDays, metaRefreshNonce)`는 다음을 처리합니다: (1) 차량 메타(모델, 이름) 조회, (2) 이벤트를 '점진'(최신→과거 청크 순서)으로 로드해 대시보드를 빠르게 표시, (3) 범위 변경 시 기존 이벤트 유지해 깜빡임 방지, (4) 알림(alerts) 병렬 로드, (5) 마지막 위치 스냅샷 별도 로드. 이벤트 로드 도중 일부 청크가 실패하면 `PartialLoadError`를 throw합니다(타임아웃과 구분).

**Progressive Loading / Streaming (점진 로드)**
  
› _모든 데이터를 한 번에 기다리지 말고, '첫 청크부터 표시' → 나머지 배경 로드_
  
사용자가 차량 상세 페이지에 진입하면, 먼저 최신 1일치 이벤트만 로드해서 차트를 바로 그립니다('최신→과거' 방향). 그 동안 백그라운드에서 이전 며칠치 데이터를 계속 가져옵니다. 진행률 표시(`loadProgress: { done: 100, total: 1000 }`)로 '500개 중 100개 로드됨'이라는 상태를 보여줍니다. 만약 사용자가 '전체 기간'을 조회하면 수천 개 이벤트를 기다려야 하므로, 이벤트 조회 타임아웃을 60초(`HEAVY_TIMEOUT_MS`)로 설정해 UI가 영구 정지되지 않게 합니다(경로 `/route` 조회는 더 무거워 90초 `ROUTE_TIMEOUT_MS`). 범위 변경 시(`from`, `to` 매개변수)에는 vehicle을 undefined로 리셋하지 않아서 대시보드가 깜빡이지 않습니다(기존 데이터 유지, 새 이벤트로 점진 교체).

**Context API (전역 상태)**
  
› _로그인 정보, 언어 설정처럼 '모든 화면에서 필요한' 데이터를 한 곳에 저장해 prop drilling 피하기_
  
만약 로그인 정보를 prop으로만 전달하면, 최상위 컴포넌트(layout)에서 여러 단계를 거쳐 깊은 자식까지 내려줘야 합니다(prop drilling). React Context는 이를 피하도록, 데이터를 '중앙 저장소'에 놓고, 필요한 컴포넌트가 `useAuth()` 훅으로 직접 가져갑니다. TeslaFleet은 `AuthProvider` (로그인 계정, 역할, 로그아웃)와 `I18nProvider` (언어 선택, 번역 함수)를 context로 관리합니다. `LayoutShell`에서 `<I18nProvider><AuthProvider><AuthGate>{children}</AuthGate></AuthProvider></I18nProvider>`로 감싸서, 모든 자식이 접근 가능하게 합니다.

**AuthProvider / useAuth (로그인 게이팅)**
  
› _사용자가 로그인했는지 확인하고, 로그인 안 했으면 /login으로 보내기_
  
앱 시작 시 `AuthProvider`가 `/auth/account/me` API를 호출해서 현재 세션의 계정 정보를 가져옵니다. 응답에서 `account` (null=로그아웃, {id, role, ...}=로그인), `auth_enforced` (서버가 인증을 강제하는지 여부), `must_change_password` (초기 로그인 후 비번 변경 필수)를 확인합니다. 계정이 없고 `enforced !== false`이면 '로그인 필요' 상태로 표시합니다. `AuthGate` 컴포넌트가 이를 보고 경로를 분기합니다: /onboard와 /login은 로그인 불필요, 그 외는 로그인 필수. 데이터 요청 중 401 응답이 오면(세션 만료 등) 'tf:unauthorized' 이벤트를 window에 쏘고, AuthProvider가 감지해서 account=null + enforced=true로 설정해 로그인 화면으로 강제 이동합니다. 역할(`role`)은 'admin'(전체 관리) 또는 'manager'(자기 고객사만)입니다.

**I18nProvider / dict.ts (다국어 번역)**
  
› _사용자가 언어를 선택하면, 모든 화면의 텍스트가 한국어↔영어로 바뀌기_
  
TeslaFleet은 한국어(ko)와 영어(en)를 지원합니다. 모든 사용자 보이는 텍스트는 `/lib/i18n/dict.ts`에 정의됩니다: `"fleet.title": { ko: "메인 현황", en: "Fleet" }`. 컴포넌트가 `const { t } = useI18n()`로 훅을 가져와서 `t("fleet.title")`이라고 호출하면, 현재 언어에 맞는 텍스트를 얻습니다. 사용자가 언어를 바꾸면 I18nProvider의 lang state가 변경되고, 모든 컴포넌트가 재렌더링되어 새 언어로 표시됩니다. 언어는 1년 유지되는 쿠키에 저장됩니다 (SameSite=Lax로 CSRF 보호). 에러 메시지도 `errKey` (번역 키)와 `errRaw` (서버 원문)을 분리 저장해서, 언어 전환 시 stale 문제를 피합니다.

**URL Query Parameters (주소 상태 저장)**
  
› _선택사항(필터, 날짜 범위)을 주소(?customer_id=c1&from=2024-01-01)에 저장해서 새로고침·공유 가능하게_
  
`useSearchParams()`는 현재 URL의 `?key=value&...` 부분을 읽고, `useRouter().replace()`로 수정합니다. 예: 고객사 필터를 바꾸면 `/?customer_id=c1`로 URL을 갱신합니다. 사용자가 이 링크를 공유하거나 페이지를 새로고침해도 같은 필터가 적용됩니다. 차량 상세 페이지의 날짜 범위도 쿼리 파라미터로 저장돼서, 뒤로 가기 시 이전 범위가 유지됩니다. 이렇게 하면 '상태'가 URL에 저장돼서, 북마크·공유가 쉬워집니다. localStorage도 보조적으로 사용해서(고객사 필터), 여러 탭 간 필터 일관성을 유지합니다.

### 성능 최적화 — 화면을 빠르게 로드하고 부드럽게 조작하기

_TeslaFleet은 Google Maps SDK와 차트 같은 무거운 라이브러리를 로드해야 하므로, 화면 표시 시간(LCP)과 상호작용 반응성(INP)을 최적화합니다._

**Dynamic Import / Code Splitting (ssr: false)**
  
› _무거운 라이브러리(Google Maps, Chart.js)를 처음엔 로드 안 하고, 필요할 때만 로드_
  
Google Maps 라이브러리는 ~50KB 이상인데, 메인 페이지 초기 로드에 포함되면 JS 번들이 무거워져서 첫 화면(LCP)이 느려집니다. `const MapComponent = dynamic(() => import('...'), { ssr: false })`를 쓰면, 메인 번들에서 제외되고 사용자가 메인 페이지에 들어온 후 '지금 Maps 라이브러리를 가져가'라고 백그라운드에 요청합니다. `loading: <Skeleton />`으로 로딩 중 플레이스홀더를 보여줍니다. ssr:false는 정적 export 방식에서는 큰 의미가 없지만(어차피 클라이언트에서 실행), 라이브러리 분리의 신호로 사용됩니다. TelemetryChart와 VehicleRouteMap이 동적으로 로드됩니다.

**LCP (Largest Contentful Paint) / 첫 화면 표시 속도**
  
› _사용자가 페이지에 들어온 후, '가장 중요한 콘텐츠'(지도, 차트 등)가 보이기까지 걸리는 시간_
  
Google의 '웹 핵심 지표(Web Vitals)'에서 LCP는 2.5초 이내를 '좋음'으로 평가합니다. TeslaFleet은 Google Maps와 Chart.js를 동적 로드로 분리해서, HTML 뼈대와 목록이 먼저 보입니다. 이후 JS 번들(~700KB)이 도착하고 실행되면, 지도와 차트가 렌더링됩니다. 레이아웃 시프트(shifting, 콘텐츠가 움직임)를 방지하기 위해 로딩 중 `<div className="h-72 border-bg-card" />`로 공간을 미리 예약합니다. 쿠키 기반 테마(dark/light/OLED 등)도 초기 HTML의 `<script>` 태그로 **DOM 파싱 전에** 적용해서 'flash of wrong theme(깜빡임)'을 방지합니다.

**Cache (localStorage, 쿠키, HTTP 캐시)**
  
› _자주 쓰는 데이터(고객사 필터, 테마, 언어)를 브라우저 저장소에 저장해서 매번 서버 호출 없이 빠르게 로드_
  
localStorage는 JavaScript에서 key-value 문자열을 저장하는 브라우저 저장소(용량 ~5MB, 사이트별 격리). `localStorage.setItem("teslafleet_theme", "dark")`로 테마를 저장하면, 다음에 방문할 때 `localStorage.getItem("teslafleet_theme")`으로 복원됩니다. TeslaFleet은 고객사 필터(`customerFilter.ts`)를 localStorage에 저장해서, 다른 페이지로 이동했다가 돌아와도 필터가 유지됩니다. 쿠키도 비슷하지만, 매 HTTP 요청에 자동 첨부되므로 (서버도 볼 수 있음), HttpOnly 보안 쿠키(`__Host-tf_account`)로 세션을 저장합니다. 정적 Export 빌드 시 HTML/CSS/JS를 nginx에서 '오래 캐시'(max-age=31536000)로 설정하면, 재방문 시 네트워크 요청 없이 로컬 파일에서 로드됩니다.

**useMemo / useCallback (렌더링 최적화)**
  
› _불필요한 재계산과 자식 재렌더링을 방지해서 버벅거림 없이 부드럽게 상호작용_
  
메인 페이지에서 고객사 필터를 바꾸면, 차량 목록과 지도 마커가 갱신됩니다. 이때 `vehicles` 배열을 `useMemo(() => [...필터링])`로 감싸면, 필터가 바뀌지 않으면 같은 배열 참조를 유지합니다. 자식 컴포넌트가 prop을 객체 동등성(`===`)으로 비교하므로, 같은 배열이면 '아, 안 바뀌었군' 하고 재렌더링을 스킵합니다(React.memo 사용 시). 함수도 마찬가지로 `useCallback`으로 고정해서, 매번 새 함수 객체를 만들지 않습니다. page.tsx의 `handleCustomerChange` 콜백이 useCallback으로 감싸여 있어서, 필터 드롭다운의 onValueChange prop이 안정적입니다.

**ResizeObserver / Scroll Anchor (스크롤 위치 보존)**
  
› _리스트에 항목이 추가·삭제될 때, 사용자가 읽던 위치가 움직이지 않게 하기_
  
차량 상세 페이지에서 이벤트를 점진 로드하면, 새 이벤트가 위에 추가됩니다. 만약 수정이 없으면 사용자는 원래 위치에 그대로 있어야 하는데, DOM이 변하면 브라우저의 자동 scroll anchor가 작동하지 않을 수 있습니다(sticky 헤더, 자주 변하는 콘텐츠). `LayoutShell.tsx`의 `usePreserveScrollAnchor`가 viewport 상단에서 30% 높이의 요소를 '기준 anchor'로 잡고, 콘텐츠가 추가될 때마다 scrollTop을 보정해서 그 요소의 위치를 고정합니다. ResizeObserver와 MutationObserver를 함께 써서, DOM 변화를 감지하고 requestAnimationFrame으로 디바운싱합니다(초당 60회 레이아웃 계산 방지).

**Debounce / Throttle (이벤트 최적화)**
  
› _스크롤·입력·리사이즈처럼 자주 발생하는 이벤트를 '최대 몇 번만' 처리하도록 제한_
  
사용자가 페이지를 스크롤하면 scroll 이벤트가 초당 60회 이상 발생합니다. 매번 처리하면 layout thrashing(레이아웃 재계산이 반복되며 성능 저하)이 일어납니다. requestAnimationFrame으로 debounce하면, 최대 초당 60회까지만 처리됩니다(브라우저 refresh rate). TeslaFleet의 scroll anchor는 `onScroll` 이벤트를 감지하지만, 매번 captureAnchor()를 호출하지 않고 requestAnimationFrame으로 감싸서, 다음 프레임에만 1회 실행합니다. 이를 'rAF debounce'라 부르며, 부드러운 애니메이션을 유지하면서도 CPU 사용량을 줄입니다.

**Tree Shaking / 번들 크기 최소화**
  
› _사용 안 하는 코드를 최종 번들에서 제거해서 용량을 줄이기_
  
TeslaFleet은 `@radix-ui` 컴포넌트 라이브러리를 사용하는데, 모든 컴포넌트를 번들에 포함할 필요는 없습니다. 사용한 컴포넌트만(Dialog, Select, Popover 등) 번들링되고, 사용 안 한 건 webpack/turbopack이 제거합니다. 이를 'tree shaking'이라 부릅니다. tsconfig.json의 `"skipLibCheck": true`로 node_modules 타입 체크를 스킵해서 빌드 시간을 단축합니다. 프로덕션 번들 크기는 ~700KB (gzip ~200KB)이며, nginx에서 gzip 압축을 활성화하면 네트워크 전송이 빨라집니다.

### 빌드 및 배포 — 코드를 테스트하고 실제 사용자에게 배포

_개발자가 작성한 TypeScript·React 코드는 그대로 실행 불가능하므로, 빌드 과정을 거쳐 브라우저가 이해할 수 있는 HTML/CSS/JS로 변환됩니다._

**npm / package.json (의존성 관리)**
  
› _프로젝트가 필요한 라이브러리(React, Tailwind, Google Maps 등)를 관리하는 파일과 도구_
  
`package.json`은 프로젝트의 메타데이터(이름, 버전)와 스크립트(npm run dev, npm run build)를 정의합니다. `dependencies`는 실제 앱 실행에 필요한 라이브러리 (next, react, react-dom, tailwindcss, @vis.gl/react-google-maps 등), `devDependencies`는 개발·빌드 시에만 필요한 도구(typescript, @types/* 타입 정의)입니다. npm install을 실행하면, node_modules 폴더에 모든 라이브러리가 설치되고, `package-lock.json`이 정확한 버전을 기록합니다(팀원이 같은 버전을 설치하도록). package.json에서 `^15.1.4` (^는 minor 업데이트 가능)로 표기하면 자동 업그레이드 대상입니다.

**TypeScript Compiler (tsc) / 타입 체크**
  
› _코드의 모든 타입 오류를 찾아 '문법 실수'를 컴파일 단계에서 차단_
  
`npm run build`는 먼저 `tsc --noEmit`을 실행합니다 (--noEmit은 파일 생성 안 함, 타입 체크만 수행). TypeScript 컴파일러가 모든 .ts/.tsx 파일을 읽고, 타입 일관성을 확인합니다. 예: `const x: number = "hello"`라고 쓰면 '문자열을 숫자로 할당 불가'라고 에러를 냅니다. 타입 체크 통과해야 다음 단계(next build)로 진행됩니다. tsconfig.json의 `"strict": true`는 가장 엄격한 설정으로, null 체크, 암시적 any 금지 등을 강제합니다.

**Next.js Build / Static Export**
  
› _React 컴포넌트와 설정을 읽고, 사전 구축된 HTML/CSS/JS 파일들을 /out 폴더에 생성_
  
`npm run build` → `next build`가 실행되면, Next.js가 다음을 수행합니다: (1) 모든 경로(/vehicles, /admin/customers 등)를 미리 정적 HTML로 생성, (2) React 컴포넌트를 메타데이터 제거하고 최적화(minify), (3) CSS를 bundling해 .css 파일 생성, (4) 라우트별로 공유 JS 청크 자동 분리. 결과는 /out 폴더(정적 HTML/CSS/JS)이며, 별도 Node.js 서버 없이 nginx 같은 정적 파일 서버에만 올리면 됩니다. 동적 경로(getServerSideProps)는 static export와 호환 불가이므로, TeslaFleet은 SPA 방식(클라이언트가 /api/v1 호출)으로만 구축되었습니다.

**Build Gate / Pre-commit Hook (자동 검사)**
  
› _빌드 전에 타입 오류, 린트 위반 등을 자동 검사해서 망가진 코드가 배포되지 않도록_
  
TeslaFleet의 build 스크립트는 `tsc --noEmit && next build`로, 타입 체크에 실패하면 next build는 실행되지 않습니다(&&는 직렬 실행, 첫 명령 실패 시 중단). CI/CD 파이프라인(GitHub Actions 등)이 이 스크립트를 실행해서, 타입 오류나 빌드 실패 코드가 main 브랜치에 merge되지 않도록 합니다. pre-commit hook으로 개발자의 로컬 git commit 단계에서도 빌드 검사를 할 수 있습니다.

**NEXT_PUBLIC_* 환경 변수 (빌드 시간 설정)**
  
› _API 서버 주소, 기능 플래그 등을 코드 변경 없이 빌드 시점에 주입_
  
`NEXT_PUBLIC_API_BASE_URL` 같은 변수를 `.env.production`에 정의하면, 빌드 시점에 번들에 bake됩니다. 로컬 개발 시 빈 문자열이면 `/api/v1`(relative path, 같은 오리진 nginx 프록시)를 사용하고, 프로덕션에서 다른 API 서버를 가리킬 수 있습니다. 주의: NEXT_PUBLIC 접두어가 없으면 클라이언트 코드에서 접근 불가(보안). 민감한 API 키는 서버 환경 변수만 쓰고 번들에 노출하지 않습니다(TeslaFleet은 서버가 없으므로 불필요).

**Docker / 컨테이너 배포**
  
› _앱과 필요한 모든 의존성을 이미지로 패킹해서, 어디서나 같은 환경에서 실행_
  
TeslaFleet 프로젝트에 Dockerfile이 있으면, `docker build -t teslafleet:latest .`로 이미지를 생성하고, `docker run -p 80:3000 teslafleet:latest`로 컨테이너를 실행합니다. 컨테이너는 격리된 리눅스 환경으로, 호스트의 다른 앱과 충돌하지 않습니다. 클라우드(AWS ECS, Google Cloud Run, Kubernetes)에 배포할 때는 이 이미지를 push해서, 자동 스케일링·헬스 체크·로드 밸런싱 등의 인프라 이점을 얻습니다.

### UI 컴포넌트 라이브러리 — 버튼, 입력칸, 드롭다운 등을 빠르고 일관되게 만들기

_TeslaFleet은 shadcn/ui(Radix UI + Tailwind CSS)를 기반으로, 웹 접근성(a11y)과 다크 모드를 지원하는 컴포넌트들을 사용합니다._

**shadcn/ui / Radix UI (컴포넌트 라이브러리)**
  
› _접근성·키보드 조작이 강력한 Dialog, Select, Popover 등 저수준 컴포넌트들의 모음_
  
shadcn/ui는 프리빌트 컴포넌트 라이브러리가 아니라, 개발자가 자신의 프로젝트에 복사-붙여넣기하는 '코드 스니펫'입니다. Radix UI의 저수준 로직(포커스 관리, ARIA 라벨, 키보드 이벤트)을 제공하고, Tailwind CSS로 스타일을 입혀줍니다. TeslaFleet이 import하는 `@radix-ui/react-dialog`, `@radix-ui/react-select` 등이 바로 이것입니다. 예: `<Select><SelectTrigger><SelectValue/></SelectTrigger><SelectContent><SelectItem>...</SelectItem></SelectContent></Select>`로 드롭다운을 만들면, 스크린 리더 사용자도 화살표 키로 항목을 선택 가능하고, 명확한 ARIA 역할이 자동 부여됩니다.

**Tailwind CSS (유틸리티 CSS 프레임워크)**
  
› _미리 정의된 class들(flex, text-lg, bg-red-500 등)을 조합해서 스타일을 빠르게 적용_
  
기존 CSS는 `.my-button { background: blue; padding: 10px; ... }` 같은 클래스를 정의해야 하지만, Tailwind는 이미 수천 개 유틸리티 클래스를 제공합니다. `<button className="bg-blue-500 px-4 py-2 rounded">Click</button>`처럼 원하는 스타일을 조합하면 끝입니다. 개발 시 속도가 빠르고, 빌드 시 사용한 클래스만 CSS에 포함되어 최종 파일 크기도 작습니다. TeslaFleet은 Tailwind **v4**를 쓰며, `globals.css` 첫 줄에 `@import "tailwindcss";` 한 줄만 선언하면 Tailwind가 모든 스타일을 주입합니다(v3의 `@tailwind base/components/utilities` 3줄 지시어를 대체). 색상·테마 커스터마이즈도 별도 `tailwind.config.js` 파일 없이 `globals.css`의 `@theme inline` 블록과 CSS 변수(`:root`, `.dark` 등)로 정의합니다.

**Dark Mode / Theme (테마 시스템)**
  
› _사용자가 다크/라이트 모드를 선택하면, 모든 화면의 배경·텍스트 색이 자동으로 바뀌기_
  
TeslaFleet은 7가지 테마를 지원합니다: light, dark, hc(고대비), sepia, solarized, nord, oled. 사용자가 ThemeToggle에서 선택하면, `localStorage.setItem('teslafleet_theme', 'dark')`에 저장되고, `<html className="dark">` 클래스가 동적으로 변경됩니다. CSS 변수(`--background`, `--foreground` 등)와 Tailwind의 selector variants(`dark:bg-slate-900`)로, dark 클래스가 있을 때만 어두운 색이 적용됩니다. globals.css에 `:root { --background: #ffffff; } html.dark { --background: #000000; }`로 정의하면, 모든 컴포넌트가 자동으로 테마를 존중합니다. 초기 로딩 시 FOUC(깜빡임) 방지를 위해 layout.tsx에서 `<script dangerouslySetInnerHTML>`으로 DOM 파싱 전에 테마를 적용합니다.

**lucide-react (아이콘 라이브러리)**
  
› _깔끔한 SVG 아이콘(검색, 메뉴, 체크 등)을 React 컴포넌트로 간편하게 사용_
  
`import { ChevronRight, X, Loader2 } from 'lucide-react'`로 가져와서, `<ChevronRight size={20} />`처럼 JSX로 렌더링합니다. 모든 아이콘은 SVG이라 확대해도 선명하고, color·size 같은 props로 커스터마이즈 가능합니다. 심볼 import가 tree shaking 대상이라, 사용한 아이콘만 번들에 포함됩니다.

**Accessible (a11y) / ARIA**
  
› _스크린 리더 사용자, 키보드 전용 사용자가 앱을 사용할 수 있도록 설계_
  
Accessible의 약자가 a11y(a + 11글자 + y)입니다. Radix UI와 shadcn/ui 컴포넌트는 기본적으로 aria-label, aria-describedby, role 같은 ARIA 속성이 자동 부여됩니다. 예: `<button aria-label="메뉴 열기">☰</button>`는 스크린 리더에게 '메뉴 열기' 버튼이라고 설명합니다. TeslaFleet은 `<aside aria-label="차량 목록">` 같은 semantic HTML과 ARIA를 사용해서, 시각 장애인도 접근 가능하게 설계되었습니다.

### 실시간 데이터 및 통신 — 차량의 위치·배터리 상태를 계속 업데이트

_TeslaFleet의 정보는 Kafka(메시지 큐), 데이터 레이크(Lakehouse)에서 오며, 프론트는 주기적으로 데이터를 폴링하거나 WebSocket으로 실시간 업데이트를 받습니다._

**Telemetry(텔레메트리) / Sensor Data**
  
› _차량이 계속 보내는 위도·경도·배터리·온도 같은 센서 데이터_
  
Tesla 차량은 주행 중/정차 중 계속 센서 정보를 서버에 전송합니다. TelemetryEvent는 `{ timestamp, latitude, longitude, battery_level, soc, temperature, gear, speed, ... }`를 가집니다. 데이터 출처는 3가지: 'live'(실시간 차량 전송), 'seeded'(과거 dump 데이터), 'simulated'(테스트용 시뮬레이터 생성). TeslaFleet은 이 이벤트들을 시계열 차트(배터리 추세), 지도(경로), 타임라인(알림)으로 표시합니다.

**Kafka (메시지 큐 / Event Streaming)**
  
› _테슬라 차량에서 계속 들어오는 이벤트들을 중간에 모아두었다가, 백엔드·데이터 파이프라인이 순서대로 처리_
  
Kafka는 분산 메시지 큐로, 원본(producer)이 메시지를 계속 쏘고, 소비자(consumer)들이 구독해서 처리합니다. TeslaFleet에선 차량이 producer(이벤트 전송), 백엔드 API 서버와 Lakehouse 파이프라인이 consumer(저장·변환)입니다. Kafka lag는 '최신 메시지와 우리가 처리한 메시지 사이의 차이'를 나타냅니다. lag가 크면 '실시간성 지연'을 의미하며, 프론트의 KafkaLagCard에서 시각화합니다.

**Lakehouse / Data Lake (데이터 저장소)**
  
› _구조화되지 않은 대량의 데이터(수십억 테이메트리 이벤트)를 저장하고 분석하는 저장소_
  
기존 데이터베이스(SQL)는 구조가 고정되어야 하지만, 데이터 레이크는 JSON, Parquet, CSV 등 다양한 형식을 저장합니다. Lakehouse = 데이터 레이크 + 쿼리 엔진(일반적으로 DuckDB·Trino 등)인데, **이 프로젝트는 AWS Athena(쿼리)·Glue Spark(ETL)·Iceberg(테이블 포맷)**를 씁니다. TeslaFleet은 수년치 차량 이벤트를 여기에 저장하고, 사용자가 '작년 6월 배터리 추세'를 요청하면 빠르게 집계해 응답합니다. 이를 'telemetry backfill'이라고도 부릅니다.

**Polling (주기적 조회)**
  
› _일정 간격(예: 10초)으로 '/api/v1/vehicles/latest' 같은 엔드포인트를 반복 호출해서 최신 데이터 가져오기_
  
WebSocket이 없으면, 클라이언트가 '혹시 업데이트 있나?' 라고 주기적으로 서버에 물어봅니다. TeslaFleet 메인 페이지의 통계 카드(Kafka lag, 데이터 품질)는 주기적으로 폴링해서 새로고침됩니다. 많은 클라이언트가 동시에 폴링하면 서버 부하가 커지므로, 백엔드는 각 엔드포인트별로 캐시 시간(예: 10초)을 설정해서 중복 조회를 줄입니다.

**WebSocket (양방향 실시간 통신)**
  
› _한 번 연결되면 서버에서 직접 클라이언트에 메시지를 보낼 수 있는 프로토콜_
  
HTTP는 요청-응답이지만, WebSocket은 지속 연결로 양쪽이 언제든 메시지를 보낼 수 있습니다. 폴링보다 효율적이어서, 라이브 대시보드(실시간 위치, 배터리 상태)에 자주 쓰입니다. TeslaFleet은 아직 WebSocket을 구현하지 않았으나, 향후 실시간 기능 추가 시 고려 대상입니다.

**Rate Limiting (속도 제한)**
  
› _한 사용자가 너무 자주 API를 호출하지 못하도록, '분당 최대 N회' 같은 제한을 둠_
  
무분별한 API 호출은 서버를 마비시키므로, 백엔드는 보통 '분당 1000 요청' 같은 제한을 둡니다. TeslaFleet 프론트는 자신의 호출을 관리해서, 불필요한 요청을 줄입니다(polling 간격 설정, debounce 등). 만약 제한을 초과하면 429 (Too Many Requests) 응답이 오고, 프론트는 사용자에게 '일시적으로 사용량이 많습니다' 메시지를 보여줍니다.


---

## ⚙️ BackEnd — 화면 뒤에서 일하는 서버

> 화면의 요청을 받아 데이터베이스와 주고받고, 로그인·권한·차량 데이터 적재를 처리하는 부분입니다.

### 웹 요청 - API 계층

_사용자의 브라우저나 앱이 보내는 요청이 서버에서 처음 만나는 계층입니다. 누가인지 확인하고, 어떤 라우트로 보낼지 결정합니다._

**FastAPI(빠른API)**
  
› _웹 서버를 만드는 파이썬 틀. 요청을 받아 코드가 실행되게 해줍니다._
  
TeslaFleet 백엔드의 중심입니다. FastAPI는 '빨리(Fast)' 만들고 '자동 설명서(API Docs)'를 만드는 웹 프레임워크예요. 사용자가 브라우저에서 버튼을 누르거나 앱이 데이터를 요청하면, FastAPI가 그 요청을 받아서 어떤 Python 함수를 실행할지 결정합니다. 응답도 FastAPI가 정리해서 돌려줍니다.

**엔드포인트(API 출입구)**
  
› _API의 입구. 주소처럼 각각 역할이 다릅니다. 예: /api/v1/vehicles = 차량 목록, /api/v1/auth/account/login = 로그인(모든 경로에 `/api/v1` prefix)._
  
엔드포인트는 HTTP 주소의 경로(path)예요. 은행 창구처럼 '환전 창구', '통장 개설 창구'가 따로 있듯이, 서버의 엔드포인트도 역할마다 따로 있어요. '/api/v1/vehicles' 가면 차량 목록을 얻고, '/api/v1/auth/login' 가면 로그인하는 식입니다. TeslaFleet에서는 `/vehicles(차량)`, `/telemetry(원격 측정)`, `/auth(인증)`, `/seed(데이터 적재)` 등이 주요 엔드포인트예요.

**라우터(교통 관제 센터)**
  
› _들어온 요청을 알맞은 처리 함수로 연결해주는 것. 누가 무엇을 요청했는지 보고 어느 함수를 실행할지 결정합니다._
  
FastAPI 라우터는 요청 URL과 방법(GET/POST 등)을 보고 '아, 이건 차량 목록을 달라는 거네' 하고 알맞은 함수를 실행해요. 라우터는 `/routers/vehicles.py`, `/routers/auth.py` 같은 파일들에 정의되어 있고, 각각 다른 주제(인증, 차량, 텔레메트리)의 엔드포인트를 모아놓았어요.

**의존성(Dependency, Depends)**
  
› _한 함수가 다른 함수의 결과를 먼저 받아야 할 때 그것을 선언하는 방식. '이 함수 실행 전에 저 함수 먼저 해줘'라고 지정하는 것._
  
FastAPI의 `Depends`를 쓰면 '이 엔드포인트 함수를 실행하기 전에 먼저 인증을 확인하고 로그인한 계정 정보를 넘겨줘'라고 지정할 수 있어요. 예: `require_account`, `customer_scope` 같은 함수들이 의존성으로 붙어서 '권한 있는 사람인지?', '어느 고객사 데이터까지 봐도 되는지?' 확인합니다.

**X-Admin-Key(관리자 마스터 열쇠)**
  
› _서버 설정에 미리 저장한 특수한 암호. 로그인 없이도 백엔드 관리 작업을 수행할 수 있게 해줍니다._
  
로그인 계정이 없어도 '.env' 파일에 저장한 특수 암호열(X-Admin-Key)을 HTTP 헤더에 담아 보내면 관리자 권한으로 일할 수 있어요. 운영 스크립트가 자동으로 데이터를 정리하거나 시뮬레이션을 시작할 때 쓰입니다. 매우 비밀로 지켜야 하는 '마스터 열쇠'예요.

### 인증 & 권한 체크

_요청이 들어오면 '누구인가?', '이 사람이 이걸 볼 수 있나?' 확인하는 단계입니다. 세션, 암호 해시, 감사 로그가 여기에 관련됩니다._

**세션(Session, 방문 기록)**
  
› _로그인한 사람이 '내가 이미 확인된 사람입니다'라고 계속 증명할 수 있게 하는 토큰. 같은 쿠키를 가진 요청은 다시 비밀번호를 입력하지 않아도 인정받습니다._
  
당신이 은행에 가서 신분증으로 신원을 확인(로그인)한 후 가지는 영수증(세션 토큰)처럼, 한 번 로그인하면 매 요청마다 이 토큰을 쿠키에 담아 보내요. 서버는 쿠키 토큰을 hash해서 DB의 `account_sessions` 테이블과 비교해 '맞다, 이 사람은 확인됐다'고 인정합니다. 30일 절대 만료, 7일 유휴 만료(7일 동안 한 번도 안 쓰면 로그아웃)가 있어요. 또 24시간마다 토큰을 자동 교체(회전)해 탈취 토큰의 수명을 제한합니다.

**토큰 해시(Token Hash, 암호화된 증명)**
  
› _원래 토큰을 일방향 암호(SHA256)로 암호화한 것. DB에 원본 대신 이것을 저장해서 혹시 DB가 유출되어도 세션 위조가 불가능하게 합니다._
  
세션 토큰(32자 난수)은 쿠키에만 들어가고, DB에는 SHA256으로 해시한 64자 문자열만 저장해요. 누군가 DB를 훔쳐도 해시에서 원본 토큰을 역산할 수 없어서, 그 세션을 가짜로 만들 수 없거든요. 비유: 서명(원본 토큰)과 지문(해시)의 관계.

**scrypt(암호 해싱 알고리즘)**
  
› _비밀번호를 암호화할 때 쓰는 천천한 알고리즘. 의도적으로 느리게 만들어 무작정 맞추려는 공격을 어렵게 합니다._
  
계정의 비밀번호는 'scrypt$n$r$p$salt$hash' 형태로 저장돼요. 의도적으로 느리고 복잡한 함수라서, 공격자가 수백만 개 비밀번호 조합을 1초 안에 시도하려고 해도 불가능합니다. 비유: 은행이 금고를 열려면 '정해진 고정시간(예: 30초)'을 기다리게 하는 것처럼.

**must_change_password(비밀번호 강제 변경)**
  
› _가입하거나 관리자가 리셋한 직후 기본 비밀번호 상태를 표시하는 플래그. true면 비밀번호를 바꿀 때까지 데이터를 볼 수 없습니다._
  
새 계정이 생기거나 관리자가 비밀번호를 리셋하면 예측 가능한 임시 비밀번호가 설정돼요. 이 플래그가 true면 403 오류로 차단해서 강제로 비밀번호를 바꾸게 하고, 그 후에야 대시보드나 차량 데이터를 볼 수 있게 합니다. 보안 사각(약한 기본 비밀번호)을 없애는 거예요.

**다단계 인증(MFA · OTP 앱 2단계, v1.7.5)**
  
› _비밀번호 외에 OTP 앱(Google Authenticator·Authy 등)이 30초마다 만드는 6자리 코드를 한 번 더 입력하게 하는 보안 단계. 비번이 새어나가도 휴대폰 앱 없이는 로그인 불가._
  
로그인 시 비번이 맞아도 바로 들어가지지 않고 **5분짜리 임시 증표(챌린지 토큰)** 만 받습니다. 그 다음 `/login/verify-otp`에서 OTP 코드(또는 1회용 백업 코드)를 통과해야 세션 쿠키가 발급돼요. **TOTP(RFC 6238)** 표준이라 authenticator 앱이 QR로 비밀키를 등록하면 같은 비밀키로 양쪽이 30초마다 같은 코드를 계산합니다. 비밀키는 **KMS 봉투암호화**로 DB에 저장(평문 미저장)하고, **백업 코드 10개**는 앱 분실 대비 1회용이며, 같은 코드를 두 번 쓰는 재사용(replay)은 `mfa_last_used_step`으로 차단합니다. `ACCOUNT_MFA_ENFORCE=0`(기본)이면 등록한 계정만 OTP를 요구(점진 도입), `1`이면 전 계정 등록 의무화(미등록 시 등록 화면 강제). 등록=계정 메뉴 🛡️, 분실 복구=백업코드 또는 관리자 OTP 리셋.

**역할(Role, admin vs manager)**
  
› _계정의 권한 수준. admin은 모든 데이터/설정을 볼 수 있고, manager는 자기 고객사 데이터만 봅니다._
  
TeslaFleet의 두 가지 역할: 'admin'은 전체 시스템 관리자(모든 차량, 모든 고객사, 설정 변경 가능), 'manager'는 특정 고객사에만 배정되어 그 고객사 차량만 볼 수 있어요. 가입할 때 기본은 manager(관리자 개입으로 고객사 분배)이고, 부스트랩 시 관리자 계정만 admin입니다. **(v1.7.6) 추가 admin은 기존 admin이 `POST /admin/accounts/{id}/role`로 매니저를 승격해 만듭니다**(공개 가입은 항상 manager라 승격이 두 번째 admin을 만드는 유일 경로). 승격 시 어드민은 고객사 스코프가 없어 customer_id가 해제되고, 반대로 강등도 되지만 **마지막 어드민 강등은 전원 잠금 방지를 위해 차단**(400 last_admin)됩니다. 역할 변경 시 해당 계정 세션은 즉시 회수돼 재로그인이 필요합니다.

**customer_scope(고객사 범위 필터)**
  
› _manager 계정이 '내 고객사 데이터만' 봐야 한다고 강제하는 필터. 차량/텔레메트리 조회 시 자동으로 고객사 ID를 WHERE 조건에 더합니다._
  
manager가 로그인하면 자기 `customer_id`가 의존성으로 전달되고, 이것이 모든 데이터 쿼리의 WHERE 조건에 추가돼요. 다른 고객사 데이터를 봐도 404(존재 누설 차단)가 반환됩니다. Admin이면 scope=None이라 필터링 없이 전체를 봅니다.

**감사 로그(Audit Log, 보안 사건 기록)**
  
› _누가 언제 뭘 했는지 DB에 영구 기록하는 것. 로그인 성공/실패, 비밀번호 변경, 계정 생성 등을 추적합니다._
  
AccountAuditLog 테이블에 모든 보안 이벤트(로그인, 비밀번호 리셋, 계정 삭제, X-Admin-Key 사용 등)를 남겨요. 각 기록은 사건, 주체(이메일/시스템), 대상, IP 해시, CloudFront 위치를 포함해서 사이버 침해 시 포렌식 조사에 쓸 수 있습니다.

**IP 해시(IP Hash, 접속지 추적)**
  
› _접속한 IP를 SHA256으로 암호화한 것. 원문 IP 대신 이것을 저장해서 개인정보 보호와 동일성 비교를 동시에 달성합니다._
  
1.2.3.4 같은 IP 주소를 그대로 저장하면 개인정보(PII)를 DB에 저장하게 되니까 해시로 변환해요. 같은 IP인지 비교는 가능하지만, 해시값에서 원문 IP를 복원은 불가능합니다. 보안 포렌식용으로 원문 IP도 별도로 저장하되, admin 화면에서만 보입니다.

### 데이터 모델링 & ORM

_실제 데이터가 어떤 '표(테이블)'에 어떤 '칸(컬럼)'으로 저장되는지 정의하는 부분입니다. SQLAlchemy ORM이 Python 클래스를 데이터베이스 테이블로 변환해줍니다._

**SQLAlchemy ORM(Object-Relational Mapping, 객체-DB 변환기)**
  
› _데이터베이스 표를 Python 클래스로 표현하고, SQL을 쓰지 않고도 데이터를 다룰 수 있게 해주는 도구._
  
DB의 vehicles 테이블을 Vehicle 클래스로, telemetry_events 테이블을 TelemetryEvent 클래스로 정의해요. 그러면 `Vehicle(vin='ABC...', display_name='테슬라1')`처럼 Python 객체를 만들고 `session.add(v)`하면 자동으로 INSERT SQL이 실행됩니다. SQL 문법 배우지 않아도 DB를 다룰 수 있어요.

**모델(Model, DB 테이블 정의)**
  
› _DB의 한 테이블이 어떤 칼럼들을 가지는지 Python 클래스로 정의한 것._
  
Vehicle, TelemetryEvent, Account 같은 클래스들이 models.py에 정의돼요. 각 클래스의 속성(id, vin, timestamp 등)이 테이블의 칼럼이 되고, 데이터 타입(String, Float, DateTime 등)도 함께 정의됩니다. DB와 코드가 이 정의로 일관성을 유지해요.

**AsyncSession(비동기 세션, 데이터베이스 대화창)**
  
› _한 요청 동안 DB와 대화하는 통로. 여러 조회/수정을 모아서 한 번에 처리하고, 마지막에 commit으로 확정하거나 rollback으로 취소합니다._
  
FastAPI 요청이 들어오면 `get_session()` 의존성이 AsyncSession을 만들어줍니다. 핸들러 함수 안에서 `await session.execute(...)` 로 쿼리를 실행하고, 성공하면 `await session.commit()`으로 DB에 적용하고, 실패하면 `await session.rollback()` 으로 취소합니다. 요청이 끝나면 세션도 닫혀요.

**Mapped(타입 힌트, 컬럼 정의)**
  
› _Python 타입으로 DB 칼럼의 데이터 타입을 명시하는 것. `Mapped[str]`은 텍스트, `Mapped[float]`은 실수, `Mapped[UUID]`는 고유ID._
  
'Mapped[str]'이라고 쓰면 '이 칼럼은 문자열이고', 'Mapped[float | None]'이라고 쓰면 '이 칼럼은 실수 또는 빈값(NULL)'이라는 뜻이에요. SQLAlchemy가 이 타입 정보를 보고 DB에는 VARCHAR, FLOAT 같이 맞게 생성합니다.

**관계(Relationship, 테이블 간 연결)**
  
› _한 테이블의 행이 다른 테이블의 여러 행과 연결될 때 그 관계를 정의하는 것._
  
Vehicle 1대가 TelemetryEvent 수백만 개를 가지는 1:N 관계예요. `vehicle: Mapped['Vehicle'] = relationship(back_populates='telemetry_events')`라고 정의하면, event 객체에서 `event.vehicle`이면 바로 해당 차량 객체를 얻을 수 있습니다. 자동 JOIN이 되는 거죠.

**JSONB(JSON 칼럼, 반정형 데이터)**
  
› _PostgreSQL의 특수 칼럼 타입. 텍스트가 아니라 JSON 객체(dict) 형태로 저장되고, 효율적으로 조회/검색할 수 있습니다._
  
TelemetryEvent.raw_data와 Vehicle.latest_telemetry는 JSONB 칼럼이에요. Tesla API에서 오는 수십 개 필드들을 일일이 컬럼으로 만들지 않고, 통째로 dict로 저장하면 유연하거든요. DB에서도 `raw_data->>'speed'` 처럼 JSON 내부 키에 직접 접근할 수 있어요.

**외래키(Foreign Key, FK, 테이블 간 무결성)**
  
› _한 테이블의 ID가 다른 테이블의 행과 실제로 존재해야 한다는 제약. 없는 ID는 저장할 수 없게 합니다._
  
TelemetryEvent.vehicle_id는 Vehicle.id의 외래키예요. 존재하지 않는 차량 ID를 텔레메트리에 저장하려고 하면 DB가 거부해요(무결성 위반). ondelete 옵션으로 차량이 삭제되면 그 차량의 텔레메트리도 함께 삭제(CASCADE)하거나, 고객사가 삭제되면 계정의 customer_id를 NULL로 둘(SET NULL) 수 있습니다.

**인덱스(Index, 검색 가속기)**
  
› _DB에서 특정 칼럼의 값을 빠르게 찾기 위해 만드는 목록. 책의 색인 같은 것._
  
TelemetryEvent의 (vehicle_id, timestamp DESC) 인덱스가 있으면, '이 차량의 최신 이벤트 100개'를 조회할 때 전체 186만 행을 스캔하지 않고 인덱스로 바로 찾을 수 있어요. 인덱스는 저장 공간을 더 쓰지만, 쓰기가 많으면 느려지는 단점도 있어요.

**Pydantic(요청/응답 검증)**
  
› _HTTP 요청 본문과 응답을 Python 클래스로 정의하고, 데이터 타입과 범위를 자동으로 확인해주는 도구._
  
POST /customers 요청이 들어오면 Pydantic의 CustomerCreate 클래스가 JSON을 파싱하고, 'name은 1~64자여야 한다'는 규칙을 체크해요. 위반하면 자동으로 422 에러를 반환합니다. 응답도 VehicleListItem 같이 정의해서, '이 필드는 어떤 타입이고 NULL일 수도 있는지' 명시합니다.

### 데이터 적재 & 처리 흐름

_차량 데이터가 Tesla API, Kafka, S3에서 들어와 데이터베이스에 저장되는 과정입니다. 배치, 트랜잭션, 마이그레이션 같은 개념도 여기 들어갑니다._

**Kafka(메시지 큐, 데이터 흐름 관리)**
  
› _여러 프로그램이 데이터를 주고받을 때 '중간 정류소' 역할을 하는 시스템. Tesla API에서 온 데이터를 임시로 모아뒀다가, 백엔드가 천천히 DB에 저장할 수 있게 합니다._
  
실시간으로 들어오는 Tesla 차량 데이터(GPS, 배터리, 충전 상태 등)를 Kafka의 토픽(topic)에 저장해요: tesla_V(텔레메트리), tesla_alerts(경고), tesla_connectivity, tesla_errors. kafka_consumer.py 프로세스가 이 토픽들을 구독(subscribe)해서 데이터를 읽고 DB에 저장합니다. 만약 DB가 느려도 Kafka가 데이터를 버퍼링해주므로 손실이 없어요.

**토픽(Topic, Kafka 데이터 스트림 주제)**
  
› _Kafka 내에서 특정 종류의 데이터를 모아두는 채널. 신문의 '정치', '스포츠' 섹션처럼 주제별로 분리._
  
TeslaFleet에서는 'tesla_V' 토픽에 텔레메트리 이벤트들이 들어가고, 'tesla_alerts' 토픽에 경고 이벤트가 들어가요. 각 토픽의 데이터는 시계열로 쌓여서, '언제 추가됐는지' 순서가 보장됩니다.

**Consumer(메시지 수신자, Kafka 구독자)**
  
› _Kafka 토픽에서 메시지를 꺼내서 처리하는 프로세스. '뉴스를 매일 아침 배달받는 구독자' 같은 개념._
  
kafka_consumer.py가 메인 consumer예요. '이 토픽들을 구독할게'라고 선언하고, Kafka에서 메시지(데이터)를 가져와서 parse_message() 함수로 파싱한 후 DB에 INSERT 합니다. 배치 처리해서 여러 메시지를 모아 한 번에 DB에 적재하면 성능이 좋아요.

**배치 처리(Batch Processing, 묶음 처리)**
  
› _여러 데이터를 하나하나 처리하지 않고 묶음(배치)으로 한 번에 처리해서 속도를 높이는 방식._
  
Kafka에서 100개의 텔레메트리 메시지를 받으면, 1개씩 100번 INSERT 하는 게 아니라, 100개를 list로 모아서 `session.execute(text(...), batch_rows)` 한 번에 INSERT합니다. DB와 네트워크 왕복이 1/100으로 줄어들어 훨씬 빨라요.

**트랜잭션(Transaction, 원자적 작업 단위)**
  
› _DB에 여러 SQL을 실행할 때, 모두 성공하거나 모두 실패하게 묶어서 '부분 성공' 상태를 피하는 것._
  
Account 테이블에 행을 추가하고, AccountAuditLog 테이블에 감사 기록도 추가한다면, 둘 다 성공하거나 둘 다 실패해야 혼란이 안 생겨요. 트랜잭션으로 묶으면, 중간에 에러가 나면 커밋 직전에 ALL ROLLBACK 되어 양쪽 다 변경되지 않습니다.

**commit(커밋, 변경 확정)**
  
› _DB 트랜잭션을 최종 확정해서 실제로 데이터가 저장되게 하는 명령. 이 전까지는 임시 상태._
  
AsyncSession에서 여러 `session.add()`, `session.execute()` 등을 하면, 메모리에만 쌓여 있어요. `await session.commit()`을 하면 그때 비로소 DB 파일/디스크에 쓰여집니다. 은행에서 '출금'을 누르기 전에는 확정되지 않는 것처럼.

**rollback(롤백, 변경 취소)**
  
› _트랜잭션 시작 후 지금까지의 모든 변경을 무르고 이전 상태로 돌리는 것._
  
100개를 INSERT 하는 도중 50번째에서 에러가 나면 `await session.rollback()`으로 모든 변경을 취소해요. 그러면 처음 50개도 저장되지 않습니다. 'all or nothing' 원칙을 유지합니다.

**SAVEPOINT(임시 체크포인트, 부분 롤백)**
  
› _트랜잭션 안에서 임시 '복구 지점'을 만들어서, 한 부분이 실패해도 전체는 안 망가지게 하는 것._
  
Kafka consumer가 100개 메시지를 배치로 처리할 때, 각 메시지마다 `async with session.begin_nested():` (SAVEPOINT)로 감싼다면, 50번째 메시지가 FK violation으로 실패해도 나머지 51~100개는 저장될 수 있어요. 배치 전체가 망가지지 않으면서도 개별 poison message는 자동으로 스킵됩니다.

**Alembic(DB 구조 변경 관리, 마이그레이션)**
  
› _DB 스키마(테이블 구조)를 버전 관리하는 도구. 새 칼럼을 추가하거나 테이블을 만들 때 변경 이력을 남기고, 이전 버전으로 돌릴 수도 있습니다._
  
'이번 배포에서 vehicles 테이블에 data_source 칼럼을 추가한다'는 변경을 alembic/versions/0018_add_data_source.py 파일로 만들어요. 이 파일이 '0017 이후 0018을 실행하려면 ADD COLUMN ...' SQL을 정의하고 있고, 배포할 때 `alembic upgrade head`를 실행하면 변경이 DB에 적용됩니다. 필요하면 `alembic downgrade` 로 이전 버전으로 되돌릴 수도 있어요.

**마이그레이션(Migration, 스키마 버전 업그레이드)**
  
› _DB 스키마를 한 버전에서 다음 버전으로 변경하는 과정. 새 칼럼 추가, 인덱스 생성 같은 DDL 변경을 관리합니다._
  
TeslaFleet에서는 지금까지 50개의 마이그레이션이 있어요(0001~0050, 주석에 언급된 Alembic 0018, 0022, 0030 등). 각각 테이블 구조 변경을 기록하고 있어서, 누군가 '예전에 차량을 고객사에 분배하는 기능이 언제 들어왔어?'라고 물으면 'Alembic 0030'이라고 답할 수 있고, 그 변경이 정확히 뭔지 파일을 열어 확인할 수 있습니다.

**boto3(AWS S3 & KMS 클라이언트)**
  
› _Amazon AWS의 S3(클라우드 저장소)와 KMS(암호화 키 관리)를 Python에서 다룰 수 있게 해주는 라이브러리._
  
TeslaFleet의 과거 데이터(dumps/)와 월별 토픽 백업(topics/year=YYYY/month=MM/)이 S3에 저장돼 있어요. seed.py 라우터가 boto3를 쓰면서 S3에서 파일을 읽고 리스트를 조회합니다. 또한 cryptography 라이브러리와 함께 OAuth 토큰을 KMS로 암호화해서 DB에 저장합니다(envelope encryption).

**데이터 출처(Data Source, live vs seeded vs simulated)**
  
› _차량 데이터가 어디서 왔는지 표시하는 태그. live(실시간 Tesla), seeded(과거 dump), simulated(자체 시뮬레이션)._
  
Vehicle 모델의 data_source 칼럼이 이것을 저장해요. 실시간 Tesla에서 Kafka로 들어온 데이터는 'live', S3 dump 파일에서 적재한 과거 데이터는 'seeded', 백엔드가 만든 가짜 테스트 데이터는 'simulated'입니다. 대시보드에서 실 차량만 보거나, 과거 데이터로만 분석할 때 필터링에 쓰여요.

### 조회 & 캐싱 최적화

_대량의 데이터를 빠르게 사용자에게 보여주기 위해 쿼리를 최적화하고 캐싱하는 방법들입니다. 인덱스, 비정규화, 메모리 캐시가 주요 기술입니다._

**비정규화(Denormalization, 데이터 중복으로 빠른 조회)**
  
› _정규 데이터베이스 원칙에서 '중복을 피하라'는 걸 살짝 어겨서, 자주 쓰는 값을 미리 복사해두는 것. 쿼리를 간단하고 빠르게 만듭니다._
  
Vehicle.event_count, first_event_at, last_event_at은 비정규화 칼럼이에요. 원칙적으로는 TelemetryEvent를 COUNT/MIN/MAX로 매번 계산해야 하지만, 186만 행이 있으면 느려져요. 대신 vehicles 테이블에 미리 계산한 값을 저장하고 daily_scheduler와 startup에서 resync_vehicle_stats() 함수로 재동기합니다. 조회는 빠르지만 쓰기는 복잡해지는 trade-off죠.

**캐시(Cache, 자주 쓰는 데이터를 빠른 곳에 두기)**
  
› _DB 대신 메모리에 자주 쓰는 데이터를 복사해두고, 요청이 들어오면 DB 대신 여기서 꺼내 주는 것. 은행의 '자주 찾는 고객 서류를 창구 책상에 둔다'는 것과 같아요._
  
list_vehicles() 엔드포인트가 대시보드에서 자주 불려요. 30초마다 새로 DB를 조회하지 않고, OrderedDict인 _VEHICLES_CACHE에 결과를 30초간 저장했다가 같은 요청이 또 들어오면 캐시에서 바로 반환합니다. TTL(Time To Live, 유효 시간)이 지나면 자동으로 버리고 다시 DB에서 읽어요.

**TTL(Time To Live, 유효 시간)**
  
› _캐시된 데이터가 얼마나 오래 유효한지를 정하는 시간. 시간이 지나면 캐시를 버리고 새로 조회합니다._
  
vehicles 캐시는 TTL=30초, event_stats 캐시는 TTL=60초로 설정돼 있어요. 너무 길면 오래된 데이터를 보여주고(staleness), 너무 짧으면 캐시 이점이 없습니다. 운영 경험으로 balance를 맞춰요.

**커넥션 풀(Connection Pool, DB 연결 재사용)**
  
› _DB와의 네트워크 연결을 여러 개 미리 만들어두고 재사용해서, 매 요청마다 새로 만드는 오버헤드를 줄이는 것._
  
db.py에서 pool_size, max_overflow로 설정돼 있어요(기본 20/20). 최대 20개 연결을 유지했다가, 일시적으로 버스트가 들어오면 추가로 20개까지 더 만들 수 있습니다. 요청이 끝나면 연결을 닫지 않고 풀에 반납해서 다음 요청이 재사용합니다. **v1.8부터는 컨테이너별 환경변수(`DB_POOL_SIZE`/`DB_MAX_OVERFLOW`)로 주입**할 수 있어요 — backend·consumer가 같은 db.py 엔진 코드를 공유하는데 둘 다 20+20이면 db.t4g.small의 max_connections 여유를 압박하므로, consumer는 단일 ingest 루프라 `CONSUMER_DB_POOL_SIZE`/`CONSUMER_DB_MAX_OVERFLOW=5`(docker-compose 기본)로 축소해 총 커넥션을 줄입니다.

**pool_pre_ping(연결 health check)**
  
› _실제 쿼리를 실행하기 전에 DB 연결이 살아있는지 확인하는 기능. 혹시 네트워크가 끊었거나 DB가 재시작됐을 때 자동으로 새 연결을 만듭니다._
  
pool_pre_ping=True라고 설정했으니, DB 연결을 풀에서 꺼낼 때마다 'SELECT 1' 같은 간단한 ping을 보내서 '연결이 아직 살아있나?'를 확인합니다. 죽어있으면 새 연결을 만듭니다.

**pool_recycle(연결 갱신 주기)**
  
› _DB 연결을 일정 시간마다 닫고 새로 만드는 것. 오래된 연결의 메모리 누수나 네트워크 상태 문제를 방지합니다._
  
pool_recycle=300(5분)으로 설정해서, 5분 이상 유지된 연결은 풀에서 자동으로 버려집니다. 새 요청이 들어오면 새 연결로 진행돼요. AWS RDS의 security group timeout이나 네트워크 불안정성에 대한 대비입니다.

**carry-forward(최신 데이터 빠른 제공)**
  
› _Tesla의 delta-encoded(변한 부분만 전송) 원격 측정을 DB에 최신 스냅샷으로 저장해서, 차량 상세 조회 시 가장 최신 텔레메트리를 빠르게 조회할 수 있게 하는 것._
  
Tesla API는 속도가 바뀐 이벤트만 보내요(delta-encoded). DB에는 Vehicle.latest_telemetry에 가장 최신 '풀 텔레메트리' 스냅샷을 JSONB로 저장해서, /vehicles/{id} 조회 시 수백만 텔레메트리 행을 스캔하지 않고 이 1개 칼럼만 읽으면 '현재 배터리 ??%, 속도 ???km/h'를 바로 얻을 수 있습니다.

### 백그라운드 작업 & 스케줄링

_시간이 오래 걸리거나 반복적으로 일어나야 하는 작업들(데이터 삭제, 토큰 갱신, 통계 계산)을 동시에 처리하고 스케줄링하는 방식입니다._

**asyncio(비동기 작업 관리, 동시 처리)**
  
› _Python에서 여러 작업을 동시에 처리할 수 있게 해주는 도구. 한 작업이 DB 응답을 기다리는 동안 다른 작업을 진행할 수 있어요._
  
FastAPI는 asyncio 기반이라서 한 스레드에서 여러 요청을 동시에 처리할 수 있어요. 요청 A가 'DB에서 데이터 조회'를 기다리는 동안, 요청 B를 처리하고, 요청 C를 처리하고... 요청 A의 DB 응답이 오면 그때 A를 계속 진행합니다. 의사: 환자 A가 검사 중일 때 환자 B, C의 진료를 진행하는 것처럼.

**create_task(백그라운드 작업 발신)**
  
› _현재 요청과 상관없이 별도로 진행될 작업을 시작하는 명령. 요청 응답을 기다리지 않고 동시에 실행돼요._
  
main.py의 lifespan에서 `asyncio.create_task(_startup_resync_vehicle_stats())`라고 하면, backend 시작 시 이 함수를 별도로 비차단으로 실행합니다. 차량 통계 재동기가 끝나기를 기다리지 않고 서버가 요청을 받기 시작해요.

**graceful shutdown(우아한 종료)**
  
› _서버를 멈출 때 진행 중인 작업들을 강제로 끊지 않고 '지금 진행 중인 건 마치고 종료해'라고 신호하는 것._
  
Kubernetes나 docker-compose에서 SIGTERM(종료 신호)를 보낼 때, main.py의 finally 블록에서 진행 중인 sim 시뮬레이션, 백그라운드 delete 작업 등을 graceful_shutdown_all_sim_tasks() 같은 함수로 '안내 종료'합니다. 20초 타임아웃을 두고, 그 안에 끝나지 않으면 강제 종료합니다. 데이터 손상을 방지하는 거예요.

**daily_scheduler(일일 반복 작업 관리자)**
  
› _매일 특정 시간에 반복할 작업(token 정리, 통계 재계산, 캐시 갱신)을 관리하는 백그라운드 루프._
  
scheduled_tasks.py의 daily_scheduler_loop()가 main.py 시작 시 create_task로 실행돼요. 만료된 세션 정리, 차량 통계 재동기, event_stats 캐시 갱신 같은 일일 작업들을 수행합니다. 매 요청을 처리하는 메인 스레드를 막지 않고 별도로 진행됩니다.

**credential rotation watcher(인증정보 갱신 감시)**
  
› _AWS RDS 비밀번호 같은 보안 인증정보가 바뀌었는지 주기적으로 확인하고, 바뀌면 백엔드를 자동으로 재시작하는 감시자._
  
AWS Secrets Manager의 RDS 인증정보가 일정 주기(예: 30일)마다 자동 회전될 때, db_credential_rotation_watcher()가 LastChangedDate를 모니터링하다가 변경을 감지하면 `sys.exit(0)`으로 backend를 재시작해서 새 비밀번호를 읽게 합니다. Kubernetes의 자동 재시작 정책과 함께 작동해요.

**시뮬레이션(Simulation, 가짜 차량 데이터 생성)**
  
› _테스트나 데모 목적으로 실 Tesla 없이 가짜 차량 데이터를 생성해서 Kafka에 보내는 것._
  
sim.py 라우터가 /admin/sim/start 엔드포인트로 시뮬레이션을 시작할 수 있게 해요. streaming_simulator.py가 정해진 주행 경로(driving/charging/parking scenario)를 따라 GPS, 배터리, 속도 같은 값을 생성해서 Kafka에 publish합니다. SimRun 테이블에서 각 시뮬레이션 실행(메시지 수, 상태 등)을 추적해요.


---

## ☁️ 인프라 — 서비스가 돌아가는 클라우드 토대

> 코드가 실제 인터넷에서 돌아가도록 떠받치는 AWS 클라우드 자원과 배포 도구들입니다.

### 클라우드 기초 개념

_인터넷상에서 소프트웨어가 돌아가는 데 필요한 기본 개념들입니다. 마치 자기 집에 있는 컴퓨터 대신, '구름 위 임대 컴퓨터'를 빌려서 쓰는 것이라 생각하면 됩니다._

**AWS(Amazon Web Services, 아마존 웹 서비스)**
  
› _인터넷상의 컴퓨터·저장소·네트워크를 빌려주는 회사._
  
TeslaFleet은 AWS라는 거대 회사의 "인프라 임대" 서비스를 사용합니다. 마치 집을 소유하는 대신 전월세 집을 빌리듯이, 서버·저장소·네트워크를 월급으로 빌립니다. 이렇게 하면 처음부터 수억 원대 장비를 사사로이 살 필요가 없습니다. TeslaFleet 프로젝트 인프라(EC2, RDS, S3, Kafka 등)가 모두 AWS에서 빌린 것입니다.

**리전(Region, 지역)**
  
› _AWS 데이터센터가 위치한 지역._
  
AWS의 컴퓨터들은 서울, 도쿄, 미국, 유럽 등 전 세계 여러 곳에 떨어져 있습니다. TeslaFleet은 '서울(ap-northeast-2)'에 있는 리전을 선택했습니다. 이렇게 하면 한국 사용자가 더 빠르게 서비스에 접속할 수 있고, 한국 규제도 맞출 수 있습니다.

**VPC(Virtual Private Cloud, 가상 사설 클라우드)**
  
› _AWS 안에서 당신만의 독립적인 네트워크._
  
AWS는 여러 고객이 쓰지만, 각 고객은 '벽'으로 막힌 자기 영역(VPC)을 받습니다. TeslaFleet도 자기 VPC를 가지고 있어서, 그 안에서 마음대로 서버와 저장소를 놓을 수 있습니다. VPC 안의 컴퓨터들은 서로 안전하게 대화하고, VPC 밖의 낯선 컴퓨터는 규칙에 따라서만 접근 가능합니다.

**서브넷(Subnet)**
  
› _VPC를 더 작은 네트워크 구간으로 나눈 것._
  
VPC(큰 마을)을 여러 구(작은 마을)로 나눈다고 생각하면 됩니다. TeslaFleet은 '공개 서브넷(인터넷에 노출된 쪽)'과 '비공개 서브넷(숨겨진 쪽)'으로 나눕니다. 웹사이트 프론트(nginx)는 공개 서브넷에, 데이터베이스(RDS)는 비공개 서브넷에 두어 보안을 높입니다.

### 컴퓨팅 및 서버 (계산·처리)

_코드를 실행하고 데이터를 처리하는 '일꾼'들입니다. 전기밥솥·세탁기처럼, 일을 시키면 해주는 기계들이라고 생각하면 됩니다._

**EC2(Elastic Compute Cloud, 신축 컴퓨팅)**
  
› _AWS에서 빌리는 가상 컴퓨터._
  
TeslaFleet에는 4개의 EC2가 있습니다: ① 메인 앱 서버(웹사이트·백엔드·소비자 5개 도커, t3.small) ② Kafka 메시지 브로커(t3.medium) ③ Kafka Connect(t3.large) ④ 텔레메트리 수집 서버(t3.small). 각각은 Linux가 설치된 가상 컴퓨터처럼 작동하고, 여기에 도커 컨테이너를 설치해 앱을 돌립니다.

**인스턴스 타입(t3.small, t3.medium 등)**
  
› _EC2 컴퓨터의 '성능 등급'._
  
CPU 코어 수·메모리 크기·네트워크 속도에 따라 여러 타입이 있습니다. t3.small(2 vCPU·2GB RAM)은 작은 업무용, t3.medium(2 vCPU·4GB)은 조금 큰 업무, t3.large(2 vCPU·8GB)는 더 무거운 작업을 합니다. 마치 자동차를 경차·준중형·중형처럼 나누는 것과 같습니다.

**EBS(Elastic Block Store, 신축 블록 저장소)**
  
› _EC2에 붙여서 쓰는 저장 드라이브._
  
컴퓨터 내부의 하드디스크처럼, EC2에 데이터를 저장하는 장치입니다. TeslaFleet의 Kafka EC2에는 주 저장소(50GB) 외에 데이터 전용 EBS(100GB gp3)가 붙어 있습니다. EC2가 망가져도 EBS는 따로 보관되어 데이터 손실을 방지합니다.

**스냅샷(Snapshot)**
  
› _저장소의 '사진을 찍어' 시간에 저장해두는 것._
  
마치 카메라로 현재 상태를 사진 찍듯이, EBS의 데이터를 어떤 시점의 모습 그대로 보관합니다. TeslaFleet은 Kafka의 100GB EBS를 매일 스냅샷 찍어 7일 보존하므로, 실수로 데이터를 지워도 최대 7일 전 상태까지 복구할 수 있습니다.

**IAM(Identity & Access Management, 정체성·접근 관리)**
  
› _AWS 안에서 '누가 뭘 할 수 있는지' 정하는 권한 체계._
  
마치 아파트에서 일부 주민만 옥상에 갈 수 있듯이, AWS도 각 서비스(EC2·RDS·S3)에 누가 접근할 수 있는지 규칙을 정합니다. TeslaFleet의 app EC2는 '아마존의 S3 버킷 읽기·쓰기만 허용, 데이터베이스 건드리기는 금지'처럼 최소권한 원칙으로 설정되어 있습니다.

### 데이터 저장 및 관리

_차량 데이터, 사용자 계정, 분석 자료 등을 보관하는 창고들입니다._

**RDS(Relational Database Service, 관리형 관계형 DB)**
  
› _AWS가 관리해주는 데이터베이스._
  
엑셀처럼 표로 정리된 데이터(vehicles·vehicle_events·user_accounts 등)를 저장합니다. TeslaFleet은 PostgreSQL 16.13 RDS(t4g.small, 20GB)를 씁니다. RDS는 AWS가 '자동 백업·성능 모니터링·보안 패치'를 대신해주므로, 개발자는 데이터만 신경 쓰면 됩니다.

**PostgreSQL(포스그레SQL)**
  
› _무료로 쓸 수 있는 관계형 데이터베이스 소프트웨어._
  
행·열로 이루어진 표 형태로 데이터를 저장합니다. 엑셀처럼 보이지만, 여러 사람이 동시에 안전하게 접근 가능합니다. TeslaFleet의 모든 사용자 데이터·주행 기록이 여기 저장됩니다.

**S3(Simple Storage Service, 단순 저장소 서비스)**
  
› _AWS의 파일 창고._
  
'teslafleet-dev-raw-telemetry-XXXXX' 버킷이라는 거대한 폴더에 원본 데이터(Kafka에서 받은 JSON)를 날짜별 폴더에 나눠 저장합니다. 마치 도서관 창고처럼, '2026-06-10/topic/message1.json' 식으로 구조화되어 있습니다. 버킷은 버전 관리(삭제해도 이전 버전 보존), 암호화, 자동 정리(오래된 파일 자동 삭제) 기능이 있습니다.

**Iceberg(아이스버그, 데이터레이크 포맷)**
  
› _분석용 대용량 데이터를 S3에 정리하는 방식._
  
원본(Bronze) → 검증(Validation) → 정제(Silver) 세 단계로 데이터를 단계적으로 정제해 저장합니다. 마치 수심에 따라 층이 나뉜 빙산처럼, 위층(Silver, 깨끗하게 다듬은 것)은 분석가가 바로 쓰고, 깊은층(Bronze, 원본)은 언제든 재분석에 쓸 수 있도록 그대로 보관됩니다.

**라이프사이클 규칙(Lifecycle rule)**
  
› _파일의 나이에 따라 자동으로 처리하는 규칙._
  
'30일 지난 파일은 느린 저장소로 옮기고, 임시 파일은 며칠 뒤 삭제한다' 같은 규칙입니다. TeslaFleet은 원본 데이터(topics/)를 30일 후 STANDARD_IA(접근 빈도 낮은 저장소)로, 90일 후 GLACIER_IR(더 저렴한 콜드 저장소·즉시 꺼내 쓸 수는 있음)로 옮겨 영구 보존하고, 임시 결과(athena-results/)는 7일 후 삭제합니다. 이렇게 하면 저장비를 아낍니다. (예전엔 365일 후 DEEP_ARCHIVE로 더 보냈으나, 그러면 다시 읽을 때 복원 대기가 필요해 2026-06-18에 GLACIER_IR 영구 보존으로 바꿨습니다.)

### 메시징 및 데이터 흐름 (파이프라인)

_차량 데이터가 Kafka라는 '우체국'을 거쳐, 여러 곳으로 배달되는 과정입니다. '보내기·받기·처리'의 흐름을 관리합니다._

**Kafka(카프카, 메시지 브로커)**
  
› _데이터의 중앙 '우체국'._
  
차량에서 오는 데이터를 임시로 보관했다가, 필요한 곳(RDS, S3, 분석기)들에 전해주는 중개자입니다. Kafka가 없으면 차량마다 각 시스템에 직접 보내야 해서 복잡하고 비효율적입니다. Kafka 덕분에 '한 군데만 보내면 여러 곳이 동시에 받을' 수 있습니다.

**토픽(Topic)**
  
› _Kafka의 '편지지' 또는 '우편 카테고리'._
  
브로커에는 **5개의 토픽**이 있습니다 — 차량 원천 4종 `tesla_V`(신호값)·`tesla_alerts`(경고)·`tesla_connectivity`(연결상태)·`tesla_errors`(오류) + 데이터레이크(Bronze) 적재용 `telemetry.raw.v1`. RDS 소비자(`kafka_consumer.py`)는 **원천 4종을 구독**해 저장하고(`tesla_V`→`telemetry_events`, `tesla_alerts`→`vehicle_alerts`, connectivity/errors는 현재 로그만), `telemetry.raw.v1`은 Kafka Connect가 읽어 Iceberg 데이터레이크로 보냅니다.

**파티션(Partition)**
  
› _토픽을 여러 쪽으로 나눠 병렬로 처리하는 것._
  
편지를 우편번호로 여러 구분대에 나눠 분류하듯이, 토픽을 6개 파티션으로 나눕니다. 덕분에 여러 소비자가 동시에 빠르게 읽을 수 있습니다. 같은 VIN(차량)의 데이터는 같은 파티션에만 가도록 정렬되어, 차량별 시계열 순서가 보장됩니다.

**Producer(생산자)**
  
› _데이터를 보내는 주체._
  
TeslaFleet에서 producer는 두 가지입니다: ① 실제 Tesla 차량(mTLS 암호화해 보냄) ② `s3-archiver`(S3 원본을 다시 정제해서 'telemetry.raw.v1' 토픽으로 보냄).

**Consumer(소비자)**
  
› _데이터를 받아서 처리하는 주체._
  
TeslaFleet에는 세 종류의 소비자가 있습니다: ① `kafka-consumer`(데이터를 RDS에 저장해 '지금' 보여줌) ② `s3-archiver`(S3에 원본 백업) ③ `Kafka Connect`(Iceberg 데이터레이크에 적재).

**Consumer Group(소비자 그룹)**
  
› _같은 목적의 소비자들 모임._
  
같은 그룹의 소비자들은 '같은 데이터를 두 번 받지 않도록' 오프셋(읽은 위치)을 공유합니다. TeslaFleet의 `kafka-consumer` 그룹과 `s3-archiver` 그룹은 독립적이라, 같은 토픽을 각각 별도로 읽을 수 있습니다.

**오프셋(Offset)**
  
› _Kafka에서 '지금 읽은 위치'를 기록하는 북마크._
  
책을 읽다가 멈춘 쪽번호를 기억하듯이, Kafka도 각 소비자 그룹이 '몇 번째 메시지까지 읽었다'를 기록합니다. 덕분에 소비자가 멈췄다 다시 시작해도 빠진 부분부터 읽을 수 있습니다.

**retention(보존 기간)**
  
› _Kafka가 메시지를 얼마나 오래 보관하는가._
  
TeslaFleet의 Kafka는 메시지를 30일간 보존합니다. 그 기간 안에 소비자가 읽지 않은 메시지는 이후 자동 삭제됩니다. 너무 짧으면 느린 소비자가 데이터를 못 읽고, 너무 길면 저장소를 낭비합니다.

### 데이터 처리 및 변환 (ETL/분석)

_원본 데이터를 깨끗이 정제하고 분석하기 좋은 형태로 만드는 작업들입니다. '밀가루 -> 반죽 -> 빵' 같은 단계를 거칩니다._

**Glue(접착제, 관리형 ETL)**
  
› _AWS의 데이터 정제·변환 자동화 도구._
  
TeslaFleet에서 Glue 작업은 두 개입니다: ① Validation(매시간 :00에 Kafka에서 받은 원본을 검증) ② Silver(매시간 :30에 통과한 데이터를 신호별로 펼쳐서 저장). 작업은 자동으로 실행(EventBridge Scheduler)되어, 운영자 수작업이 거의 없습니다.

**Spark(스파크, 분산 데이터 처리)**
  
› _Glue가 내부적으로 쓰는 '병렬 처리 엔진'._
  
대용량 데이터를 여러 컴퓨터에 나눠서 동시 처리합니다. 한 컴퓨터로 1시간 걸릴 작업을 10대가 동시에 하면 6분만에 끝낼 수 있습니다. Glue가 Spark를 내부에서 관리해주므로 개발자는 SQL·Python만 쓰면 됩니다.

**EventBridge Scheduler(스케줄러, 시간표)**
  
› _정해진 시간에 작업을 자동으로 실행하는 시계._
  
'매시간 정각 Validation 실행 → 30분에 Silver 실행' 이런 스케줄을 관리합니다. 마치 시계알람처럼, 운영자가 손으로 누르지 않아도 자동 실행됩니다. 또한 admin 대시보드에서 '지금 OFF'로 토글하면, 비용이 들지 않게 정지할 수도 있습니다.

**Athena(아테나, SQL 분석)**
  
› _S3의 데이터를 직접 SQL로 분석하는 도구._
  
데이터베이스처럼 쿼리할 수 있지만, 데이터는 S3에 그대로 있어서 비용이 저렴합니다. TeslaFleet은 Athena로 '검증 실패율', '시간별 이벤트 분포' 같은 품질 지표를 주기적으로 조회합니다. 쿼리당 스캔한 데이터 크기(byte)에 따라 과금되므로, 버킷 설정(1GB 상한)으로 실수 과금을 방지합니다.

**Kafka Connect(커넥트)**
  
› _Kafka에서 다른 저장소(S3, 데이터레이크)로 자동 이동시키는 도구._
  
Kafka의 `telemetry.raw.v1` 토픽을 읽어, 자동으로 S3의 Iceberg 테이블에 저장합니다. 마치 컨베이어 벨트처럼, Kafka의 메시지가 계속 흐르면 자동으로 데이터레이크에 쌓입니다. 별도 EC2(t3.large)에서 돌아갑니다.

**메달리온 아키텍처(Medallion Architecture)**
  
› _데이터를 '원본 -> 검증 -> 정제' 3단계로 진화시키는 구조._
  
은행권처럼 순도가 높아지는 것처럼, TeslaFleet은 Bronze(원본, 100% 보존) → Validation(필수값 체크) → Silver(깨끗한 분석용)로 진화시킵니다. 각 단계는 독립적이라, Silver가 실패해도 Bronze는 항상 원본 데이터로 재분석할 수 있습니다.

**파티션(분석 데이터의 파티션)**
  
› _데이터를 날짜나 분류별로 폴더에 나눠 저장해, 빠른 조회를 돕는 것._
  
S3에 'warehouse/telemetry_signals/day=2026-06-10/'처럼 날짜별 폴더로 저장하면, 특정 날짜만 빠르게 조회할 수 있습니다. 전체를 다 스캔할 필요 없어서 Athena 비용도 줄어듭니다.

### 보안 및 비밀 관리

_데이터베이스 비밀번호, Tesla 계정 정보, 암호 키 등을 안전하게 보관하고 사용하는 방법들입니다._

**Secrets Manager(비밀 관리자)**
  
› _AWS의 '금고', 비밀 데이터를 안전하게 보관하는 서비스._
  
TeslaFleet은 여기에 보관합니다: ① RDS 접속정보(사용자명·비번) ② Tesla OAuth 자격증명 ③ Google Maps API 키 ④ telemetry CA/서버 인증서 ⑤ **Tesla 파트너 공개/개인키**(well-known 서빙 + Command Proxy 서명, 2026-06) ⑥ Basic auth 비밀번호(**v1.7.0에서 nginx Basic auth 제거 — 현재 인증은 계정 로그인, 이 시크릿은 롤백용으로만 보관**). 코드에 절대 적혀있지 않고, 런타임에 필요할 때만 fetch 합니다.

**KMS(Key Management Service, 암호화 키 관리)**
  
› _AWS의 '열쇠 보관소', 암호화 키를 관리하는 서비스._
  
차주의 Tesla 토큰(OAuth 토큰)과 **OTP(TOTP) 비밀키**는 매우 민감해서, 단순히 저장하면 안 되고 암호화해서 저장합니다. KMS는 'AES-256 봉투 암호화'라는 강력한 암호를 관리하고, app EC2만 이 키로 암호/복호할 수 있게 권한을 제한합니다.

**봉투 암호화(Envelope Encryption)**
  
› _편지를 암호로 잠그고, 그 암호 열쇠를 다시 더 강한 열쇠로 잠그는 방식._
  
①데이터(차주 토큰)를 AES-256으로 암호화 → ②그 암호 키를 KMS의 마스터 키로 다시 암호화. 이렇게 하면 누군가 데이터베이스를 훔쳐가도 마스터 키(KMS)가 없으면 열 수 없습니다.

**Secret Rotation(비밀번호 자동 교체)**
  
› _정기적으로 암호를 자동으로 새 것으로 바꾸는 것._
  
TeslaFleet의 RDS 마스터 비밀번호는 30일마다 자동 변경됩니다. Lambda 함수가 'old → new → test → finish' 절차로 안전하게 교체해, 운영자 수작업이 0입니다. 혹시 이전 비번이 새어나가도 30일 뒤면 쓸모없어집니다.

**CloudFront(클라우드프론트, CDN·웹 관문)**
  
› _AWS의 '거리두기 서비스', 전 세계 여러 곳에 사본을 두어 빠르게 전달하는 것._
  
TeslaFleet의 웹사이트는 CloudFront를 거쳐서만 접근됩니다. CloudFront는 ① 요청을 빠르게 캐싱 ② app EC2 IP를 숨기고 CloudFront IP만 노출해 직접 공격 방지 ③ DDoS 공격 필터링. 마치 경호원이 앞에 서서 먼저 검사하듯이 작동합니다.

**Security Group(보안 그룹, 방화벽)**
  
› _AWS 리소스 앞의 '가상 방화벽', 누가 어떤 포트로 접근할 수 있는지 규칙._
  
예) app EC2는 CloudFront의 IP만 포트 80 허용, RDS는 app EC2만 포트 5432 허용. 이렇게 하면 인터넷상의 낯선 사람이 RDS에 직접 접근할 수 없습니다.

**VPC Endpoint(VPC 끝점)**
  
› _AWS 서비스(Secrets Manager, S3)로 가는 '직통 터널', 인터넷을 거치지 않는 길._
  
private subnet의 Lambda나 EC2가 Secrets Manager나 S3에 접근할 때, 보안을 위해 인터넷을 거치지 않고 AWS 내부 망을 씁니다. 마치 외출하지 말고 지하 통로로 가는 것처럼, 데이터가 외부에 노출되지 않습니다.

**최소권한 원칙(Least Privilege)**
  
› _각 서비스에 필요한 최소한의 권한만 주는 원칙._
  
app EC2는 '아마존 S3의 topics/·athena-results/·deploy/ 폴더만 읽고 쓰기' 권한만 주고, warehouse/ 폴더 삭제는 절대 금지합니다. Glue 역시 필요한 S3 경로와 Glue 작업만 접근 가능합니다.

### 컨테이너 및 배포

_코드를 '박스에 담아' 어디서나 같은 환경에서 돌리는 기술입니다. 이사할 때 짐을 박스에 정리해서 옮기듯이, 앱도 컨테이너에 담아서 배포합니다._

**Docker(도커, 컨테이너 엔진)**
  
› _앱을 '포장'해서 어디서나 같은 환경에서 돌리는 기술._
  
TeslaFleet은 app EC2 한 대에 5개 도커 컨테이너를 띄웁니다: ① nginx(웹서버) ② backend(FastAPI) ③ frontend(Next.js) ④ kafka-consumer(메시지 처리) ⑤ s3-archiver(S3 백업). 각 컨테이너는 Linux + 필요 라이브러리 + 앱이 다 들어있어서, 다른 환경(맥·윈도우)에서도 같은 모습으로 돌아갑니다.

**Dockerfile**
  
› _도커 이미지 제조법._
  
마치 요리책처럼, '① Python 3.12 이미지 시작 → ② 라이브러리 설치 → ③ 코드 복사 → ④ 포트 8000 노출'처럼 순서대로 적혀있습니다. backend/Dockerfile과 frontend/Dockerfile이 각각 그들의 이미지를 만듭니다.

**이미지(Image, 컨테이너 이미지)**
  
› _도커 '설계도', 컨테이너를 만드는 템플릿._
  
Dockerfile로 이미지를 빌드하면, 그 이미지가 'ghcr.io/OWNER/teslafleet-backend:latest' 같은 주소에 저장됩니다. 이 주소로 몇 번이고 같은 환경의 컨테이너를 만들 수 있습니다.

**Docker Compose(도커 컴포즈)**
  
› _여러 도커 컨테이너를 한 번에 관리하는 도구._
  
'docker/docker-compose.yml'에 5개 컨테이너(nginx, backend, kafka-consumer, s3-archiver, frontend)의 설정을 모두 적어놨습니다. 운영자가 'docker compose up'만 치면 5개가 동시에 뜨고, 네트워크로 서로 연결됩니다.

**헬스체크(Healthcheck)**
  
› _컨테이너가 '살아있고 정상작동하는가'를 주기적으로 확인하는 것._
  
backend 컨테이너는 10초마다 'curl http://localhost:8000/health'로 생존 신호를 봅니다. 응답이 없으면 '죽었다'고 판단해 자동 재시작합니다. 덕분에 앱이 멈춰도 자가치유합니다.

**메모리 제한(Memory Limit)**
  
› _컨테이너가 쓸 수 있는 최대 RAM을 정하는 것._
  
t3.small(2GB) EC2에 5개 컨테이너가 공존하므로, 각각 메모리를 아껴서 써야 합니다. backend는 640MB, frontend는 256MB처럼 정해놓으면, 한 컨테이너가 폭주해도 다른 컨테이너는 살 수 있습니다.

**로깅(Logging, 로그 기록)**
  
› _컨테이너가 내뱉는 출력을 파일에 모아두는 것._
  
TeslaFleet은 docker compose에서 'json-file 드라이버'를 써서, 각 컨테이너의 로그를 10MB씩 3개만 보관(이전엔 무제한이라 20GB EBS가 가득 차는 사고가 났음). 로그가 남아야 문제 분석할 때 '어디서 깨졌는가'를 알 수 있습니다.

**Alembic(알렘빅, DB 마이그레이션 관리)**
  
› _데이터베이스 스키마(표 구조) 변경을 버전 관리하는 도구._
  
'alembic head 0050'은 '50번의 구조 변경을 모두 적용했다'는 뜻입니다. 0041(계정 로그인 테이블 추가) → 0042(보안 강화·감사로그 테이블 신설) → 0044(감사로그에 IP·위치 컬럼) → 0045(활성 세션에 IP·위치 컬럼) → 0046(계정 OTP 다단계 인증 컬럼) → 0047(차량 심화 분석 가속 인덱스 3종) → 0048(배터리·대기방전 분석 커버링 인덱스) → 0049(충전 세션 분석 인덱스 — 넓던 ix_te_charging을 charge_state='Charging' AND charging_power_kw>0 AND 정차 조건의 부분 인덱스 ix_te_charging_active로 교체) → 0050(자주 가는 장소 index-only scan용 커버링 인덱스 ix_te_places) 같은 변경이 순서대로 기록되어, 누가 언제 뭘 바꿨는지 추적 가능합니다.

**배포(Deployment, Deploy)**
  
› _새 버전 코드를 실제 서버에 올려서 실행시키는 과정._
  
TeslaFleet의 deploy.sh는 ① 새 이미지 빌드 → ② Secrets Manager에서 설정값(DB주소·토큰) fetch → ③ docker compose down → ④ docker compose up으로 한 번에 모두 처리합니다. 이 과정이 몇 초에 끝나도록 최적화되어 있습니다.

**Terraform(테라폼, Infrastructure as Code)**
  
› _AWS 리소스를 코드로 정의해서 자동으로 생성·관리하는 도구._
  
infra/envs/dev/main.tf 파일에 'EC2 1대 생성, RDS 만들기, S3 버킷 설정, 권한 정하기' 등을 모두 코드로 적어놨습니다. 'terraform plan'으로 무엇이 바뀔지 먼저 보고, 'terraform apply'로 실행합니다. 손으로 AWS 콘솔을 클릭하는 것보다 안전하고 추적 가능합니다.

### 모니터링 및 운영

_시스템이 잘 돌아가는지 확인하고, 문제가 나면 알려주는 기능들입니다._

**CloudWatch(클라우드워치, 감시·알람)**
  
› _AWS 서비스들의 건강 상태를 모니터링하고 알림을 보내는 서비스._
  
TeslaFleet은 RDS 저장공간(FreeStorageSpace < 2GB)이 부족하면 CloudWatch 알람이 울려서 SNS로 이메일 알림을 보냅니다. 마치 병원의 심전도처럼, 실시간으로 상태를 감시해서 문제 전에 미리 알려줍니다.

**SNS(Simple Notification Service, 간단 알림 서비스)**
  
› _AWS의 '벨 누르기', 알림을 여러 채널(이메일·SMS·웹훅)로 보내는 서비스._
  
CloudWatch 알람이 '상태 이상' 신호를 보내면, SNS 토픽(`ops-alerts`)에 가입한 이메일 주소들에게 자동으로 메일이 갑니다. admin 대시보드에서 어떤 주소들이 받을지 관리합니다.

**Metrics(메트릭, 성능 지표)**
  
› _CPU 사용률, 네트워크 I/O, RDS 저장공간처럼 시스템 상태를 숫자로 나타낸 것._
  
AWS는 모든 리소스(EC2, RDS, S3)의 메트릭을 자동으로 수집해서 CloudWatch에 저장합니다. 관리자는 그래프를 보며 '지난 며칠간 어떻게 변했는가'를 알 수 있습니다.

**SSM Session Manager(원격 접속 도구)**
  
› _AWS 내부 망으로 EC2에 안전하게 접근하는 방법._
  
Kafka나 app EC2의 상태를 확인하려고 해도, SSH 포트 22를 열 필요 없습니다. IAM 권한만 있으면 AWS 콘솔에서 직접 '터미널 열기'로 접속할 수 있습니다. 외부 포트가 닫혀있어도 됩니다.

**Log(로그, 기록)**
  
› _프로그램이 실행되면서 출력하는 텍스트 기록._
  
backend 로그에 '[2026-06-18 10:30:45] User login failed: Invalid token'처럼 시간별로 기록되어, 나중에 문제를 분석할 때 '어디서 깨졌나'를 추적할 수 있습니다.

**Audit Log(감사로그, 감시 기록)**
  
› _'누가 언제 뭘 했는가'를 기록하는 로그._
  
RDS의 account_audit_log 테이블에 '2026-06-18 admin이 로그인했다'·'admin이 user@example.com 비밀번호를 리셋했다'·'X-Admin-Key로 관리 작업을 수행했다' 같은 **계정·보안 이벤트**가 남습니다(OTP(MFA) 등록/해제/오답/백업코드 사용/리셋·로그인 성공/실패/잠금·비번 변경/리셋·고객사 분배·어드민 승격/강등·계정 생성/삭제·세션 회수 등). 보안 감시와 사후 분석에 쓰입니다. ⚠️ **데이터 조회(차량/텔레메트리 GET)는 감사하지 않습니다** — 계정 변경·인증 이벤트만 기록합니다.

**MTLS(Mutual TLS, 상호 인증서 암호화)**
  
› _클라이언트와 서버가 서로 신원을 확인하고 암호화하는 방식._
  
Tesla 차량이 telemetry EC2로 데이터를 보낼 때, 단순히 HTTPS(서버만 신원 확인)가 아니라 둘 다 인증서를 제시해서 '정말 당신이 Tesla 맞나?', '정말 당신이 우리 서버 맞나?'를 확인합니다. 가짜 차량이나 가짜 서버를 쉽게 속일 수 없습니다.


---

## 📊 데이터 — 차량 신호가 흘러 분석되는 길

> Tesla 차량이 보낸 신호가 수집→저장→정제→화면/분석까지 흐르는 데이터 파이프라인입니다.

### 1. 데이터 수집 — 차량이 보내는 신호가 모이는 길

_Tesla 차량이 실시간으로 보내는 주행 데이터가 어떻게 모이고 처리되는지를 설명하는 용어들입니다._

**텔레메트리 (Telemetry)**
  
› _차량이 자동으로 보내는 주행 데이터._
  
Tesla 차량이 속도, 배터리, 위치, 온도 등을 계속해서 시스템으로 전송하는 것을 말합니다. 마치 비행기가 비행 중에 조종실에 고도·연료·속도를 자동 보고하듯이, 차량도 운행 상황을 계속 보냅니다. 이 프로젝트에서는 이 데이터를 받아서 대시보드에 표시하고, 분석용으로 저장합니다.

**VIN (Vehicle Identification Number)**
  
› _자동차의 고유 신원증 — 17자 번호._
  
모든 차량에 부여된 고유한 번호로, 주민등록번호처럼 그 차량을 유일하게 식별합니다. 예: '5YJ3...' 또는 'LRWY...'. 이 프로젝트에서는 VIN으로 어느 차량의 데이터인지를 판별하고, 같은 차 데이터를 모아서 분석합니다. SIM-(시뮬레이션)으로 시작하는 것은 테스트용 가짜 차량입니다.

**신호 (Signal)**
  
› _차량이 한 번에 보내는 데이터 항목 하나 — 속도, 배터리, 온도 등._
  
차량이 보내는 메시지에는 여러 정보가 들어있습니다. '속도_kph', 'SOC(배터리%)', '위도/경도', '온도' 같은 것들이 각각 하나의 신호입니다. Delta-encoding이라는 기법을 써서 변한 신호만 보내므로 (다음 절 참고), 매번 모든 신호가 오는 것은 아닙니다.

**Delta-encoding (델타 인코딩)**
  
› _변한 값만 보내기 — 같은 값은 또 안 보냄._
  
차량이 매 초마다 속도·배터리·온도를 전부 보낸다면 데이터가 너무 많아집니다. 대신 Tesla는 '이전 메시지와 달라진 신호만' 보냅니다. 예를 들어 속도가 50→51km로 1km 증가했으면 '속도_신호만' 보내고, 배터리는 80%에서 안 변했으면 안 보냅니다. 이렇게 하면 네트워크 효율이 높아집니다.

**Kafka (카프카)**
  
› _데이터가 모이는 중앙 '메시지 큐' — 모든 차량의 신호가 들어왔다가 나간다._
  
Kafka는 큰 물탱크처럼 생각할 수 있습니다. 수도꼭지(차량)에서 흘려보내는 물(신호)이 여기 모였다가, 두 갈래로 나뉩니다: (1) 왼쪽 파이프 = 데이터베이스로 가서 대시보드 표시, (2) 오른쪽 파이프 = 클라우드 저장소로 가서 분석. Kafka는 중간에 '메모리'도 가지고 있어서, 잠깐 나가는 쪽이 늦어도 데이터가 사라지지 않습니다.

**Topic (토픽)**
  
› _Kafka에서 데이터 종류별 '폴더'._
  
Kafka 안에는 여러 주제의 데이터 흐름이 섞여 있어요. 이를 구분하기 위해 topic이라 부릅니다. 이 프로젝트는 차량이 보내는 4가지 원천 토픽 `tesla_V`(주행 신호), `tesla_alerts`(경고), `tesla_connectivity`(연결 상태), `tesla_errors`(오류) 외에, 데이터레이크(Bronze) 적재용 `telemetry.raw.v1`(Bronze envelope) 토픽을 더해 **총 5개**를 씁니다(처리 실패분을 모으는 DLQ `telemetry.raw.v1.dlq`는 Kafka Connect가 자동 생성). 마치 편의점에서 우유 코너, 간식 코너처럼 물건을 분류하듯이, Kafka도 데이터를 topic으로 분류합니다.

**Partition (파티션)**
  
› _하나의 topic 안에서 데이터를 여러 칸(분할)으로 나누기._
  
한 topic의 메시지가 너무 많으면 느려집니다. 그래서 topic을 여러 partition(예: 6개)으로 나누어서 동시에 처리합니다. 편지국이 우편배달을 북쪽·남쪽·동쪽·서쪽 배달원에게 나눠 주듯이, Kafka도 메시지를 여러 partition으로 분산시켜 병렬 처리합니다.

### 2. 실시간 서빙 경로 — 대시보드에 '지금 상태'를 보여주기

_차량 신호가 모인 Kafka에서 RDS라는 데이터베이스를 거쳐 화면에 표시되는 과정입니다._

**RDS (Relational Database Service)**
  
› _대시보드가 읽는 '실시간 데이터베이스' — PostgreSQL 16._
  
Kafka에서 모인 신호를 가공해서 여기 저장합니다. 마치 카페가 주문을 받은 후 주문대에 써붙이는 '현황판'처럼, RDS는 '지금 각 차량의 최신 상태'를 보관합니다. 그래서 대시보드가 빨리 조회할 수 있습니다. PostgreSQL이라는 안정적인 데이터베이스를 씁니다.

**Carry-forward (캐리포워드)**
  
› _빠진 신호를 직전 값으로 채우기._
  
Delta-encoding 때문에 차량이 안 보낸 신호가 있습니다. 예를 들어 온도가 25도에서 안 변했으면 안 옵니다. 하지만 대시보드는 '지금 온도가 몇도'인지 보여줘야 합니다. 그래서 '온도는 이전 메시지의 25도를 그대로 앞으로 당겨서' 현재 상태로 표시합니다. 마치 '연락 없으면 평화'처럼, 신호가 없으면 이전 값을 유지하는 겁니다.

**FastAPI (백엔드)**
  
› _대시보드 앱이 '지금 정보 주세요' 할 때 그걸 들어주는 서버._
  
RDS에서 '이 차의 최신 상태 100대분' 같은 요청을 받아서 데이터를 꺼내 JSON(웹이 이해하는 형식)으로 만들어 돌려줍니다. 마치 편의점 점원이 '이 상품 얼마?' 요청을 받고 가격을 알려주듯이, FastAPI는 요청에 답합니다.

**Cache (캐시)**
  
› _자주 쓰는 데이터를 빠르게 꺼내도록 미리 준비해둔 것._
  
100대 차량의 '지금 상태'를 매번 데이터베이스에서 꺼내면 느립니다. 그래서 '이 데이터는 방금 요청한 걸 60초간 기억했다가 또 누가 물으면 그걸 줄 수 있다'고 미리 정하는 것이 캐시입니다. 마치 '카페에서 자주 쓰는 잔은 손 닿는 곳에 둔다'는 것처럼, 자주 읽히는 데이터를 빠른 곳에 둡니다. 이 프로젝트에서는 live 데이터는 60초, 시뮬·test 데이터는 600초(10분) 동안 기억합니다.

**Watermark (워터마크)**
  
› _'여기까지 처리했다'는 표시 — 다음에 그 다음부터 읽으면 된다._
  
Kafka에서 신호가 계속 들어오는데, 매번 처음부터 다 읽으면 비효율입니다. 그래서 '어제 오후 3시까지 처리했으니 그 이후 신호만 읽자'고 표시하는 것이 워터마크입니다. 마치 독서를 할 때 '어제 100쪽까지 읽었으니 101쪽부터 읽자'고 북마크를 하듯이, 데이터 처리도 워터마크로 '어디까지 했는지' 기억합니다.

**At-least-once (최소 한 번 전달)**
  
› _같은 신호가 2번 올 수도 있다는 뜻 — 데이터 손실은 없지만 중복은 가능._
  
네트워크가 불안정하면 '신호 받았다'는 답변이 차량에 안 도달할 수 있어요. 그러면 차량은 '아, 받은 줄 모르고 다시 보내야 하나?' 하고 같은 신호를 또 보냅니다. 그래서 RDS에 같은 데이터가 들어올 수 있습니다. 완벽한 '정확히 1번 전달'보다는 '최소 한 번은 도착하도록' 하되, 중복은 나중에 걸러냅니다.

### 3. 데이터 저장소 — 분석을 위한 '물고기 양식장' 아키텍처

_차량 데이터를 오래 보관하고 분석하기 위해 설계된 구조입니다. 마치 종이 서류를 '원본 보관 → 정제 → 분석'으로 3단계 정렬하듯이._

**Lakehouse (레이크하우스)**
  
› _데이터 호수(Lake, 생 데이터 모음) + 데이터 창고(House, 정제 데이터 모음)의 합친 개념._
  
이전엔 데이터를 '생 저장소'와 '정제 저장소'에 따로 관리했습니다. 호수처럼 생 데이터를 모아두고, 창고에서 정제·분석했죠. 이제는 그 둘을 한 곳에 합쳤어요. 이 프로젝트는 S3(클라우드 저장소)에 Bronze → Silver 단계로 저장하되, Iceberg라는 특수 형식을 써서 데이터 신뢰성을 높였습니다.

**Bronze (브론즈)**
  
› _원본 데이터를 그대로 저장하는 첫 번째 단계._
  
차량에서 온 데이터를 검증·정제하지 않고 있는 그대로 S3에 저장합니다. 마치 박물관이 발굴한 유물을 청소하지 않은 채 보관하듯이. 따라서 나쁜 데이터도 섞여 있을 수 있습니다. 하지만 원본을 잃지 않으므로 나중에 '이 데이터 뭐였지?' 하고 다시 확인할 수 있습니다.

**Silver (실버)**
  
› _Bronze 데이터 중 '좋은 것만' 골라서 정규화·정제한 단계._
  
Bronze에서 '이 데이터 형식 맞나? 필수 필드는 다 있나?'를 검증해서 통과한 것들만 모아 깔끔하게 정렬합니다. 마치 박물관 유물을 세척·촬영·분류하듯이. Silver 데이터는 신뢰할 수 있어서 히스토리·통계·재처리의 출발점이 됩니다.

**S3 (Simple Storage Service)**
  
› _AWS의 '무한 파일 저장소' — 사진·동영상·로그처럼 뭐든 저장 가능._
  
클라우드의 큰 창고로 생각하면 됩니다. RDS는 '지금 필요한 몇 테이블'만 빨리 가져올 수 있는 작은 책상이라면, S3는 '역사 데이터를 다 보관할 수 있는 큰 도서관'입니다. 이 프로젝트에서는 Bronze(원본)·Silver(정제본)를 S3에 저장합니다.

**Iceberg (아이스버그)**
  
› _클라우드 저장소에 테이블처럼 데이터를 정렬하고 추적하는 특수 형식._
  
S3는 그냥 '파일 더미'라서, 파일이 추가·수정·삭제되면 추적이 어렵습니다. Iceberg는 데이터베이스처럼 '어떤 파일이 지금 유효한가', '언제 누가 추가했나' 같은 메타데이터를 관리해줍니다. 마치 도서관이 '어떤 책이 몇 권 있고 누가 언제 반납했는지' 기록하듯이. 덕분에 분석가가 안심하고 S3 데이터를 쿼리할 수 있습니다.

**Partition (파티션) — 저장소 관점**
  
› _데이터를 날짜별로 칸을 나눠서 저장하기 — 찾을 때 빨라진다._
  
S3에 몇 년치 데이터가 쌓이면 '2026-06-11의 데이터'를 찾기 위해 전체를 스캔하면 느립니다. 대신 '2026년 폴더 → 6월 폴더 → 11일 폴더'처럼 날짜별로 칸을 나누면, 필요한 날짜 폴더만 열면 됩니다. 이를 파티션이라 합니다.

### 4. 데이터 검증 — 나쁜 데이터 걸러내기

_Bronze 데이터가 정말 쓸 수 있는 건지 확인하고, 문제 있는 것은 따로 보관하는 과정입니다._

**Contract (계약) / Contract Validation**
  
› _'데이터가 이렇게 생겼으면 좋겠다'는 규칙 — 그걸 따르는지 확인하기._
  
예를 들어 '모든 신호는 VIN(차 번호)이 있어야 한다', '시간 정보가 파싱 가능해야 한다'는 규칙을 정합니다. 이를 contract라 합니다. 그 다음 Bronze 데이터를 차근차근 확인해서 규칙을 지켰는지 봅니다. 마치 식당이 '배달 음식은 따뜻해야 한다' 규칙을 정하고 배달 올 때마다 온도를 재는 것처럼. 이 프로젝트는 매 시간 이 검증을 자동으로 합니다.

**Validation Result (검증 결과)**
  
› _각 데이터가 'pass(통과)'인지 'fail(실패)'인지 'error(오류, 재검증 대상)' 기록._
  
Bronze의 각 신호마다 검증 결과를 저장합니다. Pass이면 Silver로 올려보내고, fail이면 quarantine(격리) 테이블에 따로 보관, error면 나중에 다시 검증 시도합니다. 마치 공항 보안 검사처럼 '정상 통과 / 금지물 적발 / 재검사 필요' 3가지로 분류합니다.

**Quarantine (격리)**
  
› _contract를 지키지 않은 데이터를 따로 보관하는 공간._
  
데이터 검증에서 fail(실패)한 것들을 여기에 모아둡니다. '이 신호는 VIN이 없어서 못 썼다', '시간 형식이 잘못됐다' 같은 이유와 함께 보관합니다. 나중에 분석가가 '왜 이 데이터가 안 됐을까?' 확인할 때 씁니다.

**DLQ (Dead Letter Queue)**
  
› _기술적으로 처리 못한 메시지를 모아두는 '죽은편지함'._
  
JSON을 파싱하다가 오류가 나거나, 네트워크에서 데이터가 깨져서 도착하면, 데이터 검증을 할 수도 없습니다. 이런 '구제 불가능한' 메시지를 따로 DLQ에 모아둡니다. 마치 우체국이 주소를 못 읽은 편지를 '반송용 편지함'에 모으듯이. 나중에 운영자가 이 편지함을 보고 원인을 조사합니다.

**Glue (글루 — AWS)**
  
› _AWS의 '데이터 정제 엔진' — Spark라는 병렬 처리 도구를 클라우드에서 쓸 수 있게 한 서비스._
  
수십억 줄의 데이터를 한 번에 처리해야 할 때, 한 컴퓨터로는 느립니다. Glue는 많은 컴퓨터를 동시에 쓰게 해줍니다. 이 프로젝트는 Glue를 써서 Bronze → Validation → Silver 단계를 매 시간 자동으로 처리합니다.

### 5. 데이터 흐름 최적화 — 효율·신뢰·안전

_데이터가 빠르고 안전하게, 중복 없이 처리되도록 하는 기법들입니다._

**Replay (리플레이)**
  
› _'이 데이터 다시 처리하고 싶은데?' — S3에 있는 원본을 다시 꺼내서 흘려보내기._
  
만약 처리 로직이 버그가 있었다면? Silver의 데이터가 틀렸을 거예요. 하지만 S3(Bronze)에는 원본이 남아있습니다. 그래서 '원본을 다시 꺼내서, 이번엔 고친 로직으로 처리해' 할 수 있습니다. 마치 영화를 찍었는데 편집이 마음에 안 들면 원본 필름을 다시 꺼내서 새로 편집하듯이.

**Dedup (중복 제거)**
  
› _같은 데이터가 여러 번 저장되지 않도록 정확히 1번만 보관하기._
  
At-least-once 때문에 같은 신호가 여러 번 들어올 수 있습니다. 예를 들어 '2026-06-11 14:32, VIN 5YJ3..., 속도 50'이 2번 올 수 있어요. Dedup은 '이미 같은 내용이 있으면 또 저장하지 말자'고 정하는 것입니다. 자연키(VIN + 시간 + 신호 내용)로 중복 여부를 판단합니다.

**Downsampling (다운샘플링)**
  
› _데이터를 걸러내서 양을 줄이기 — 예: 1초마다가 아니라 10초마다만 저장._
  
차량이 매 초마다 데이터를 보내면 데이터가 너무 많습니다. '10초 구간 데이터는 1개만 대표로 남기자' 같은 걸터내기를 downsampling이라 합니다. 마치 영화가 초당 24프레임이지만, 요약 영상은 초당 2프레임만 보여주는 것처럼. 이 프로젝트에서는 `width_bucket`이라는 함수로 시간을 구간으로 나눠서 각 구간의 대표값 1개를 뽑습니다.

**Douglas-Peucker Algorithm**
  
› _차량 경로를 간소화하기 — 불필요한 꺾임을 걸러내서 선을 단순화._
  
차량이 달린 정확한 경로는 지그재그로 구부러질 수 있습니다. 하지만 지도에 다 표시하면 복잡해요. Douglas-Peucker는 '중요한 꺾임은 살리고, 사소한 지그재그는 무시해서' 경로를 간소화합니다. 마치 구글 지도가 복잡한 실제 도로를 단순한 선으로 표시하듯이.

### 6. 운영 · 모니터링 — 시스템이 잘 작동하는지 확인하기

_데이터 처리가 중단되거나 오류가 나면 언제 알 수 있도록 하는 장치들입니다._

**EventBridge Scheduler**
  
› _AWS의 '자동 시간표' — '매 시간 정각에 데이터 검증 시작', '매 정각 30분에 Silver 처리 시작' 같은 걸 자동으로._
  
Glue 작업을 언제 실행할지 정하는 서비스입니다. 마치 회사가 '매일 아침 9시에 회의' 정하듯이, 여기서는 '매 시간 :00분에 validation 실행', '매 시간 :30분에 silver 실행' 같이 일정을 짭니다. 그러면 자동으로 Glue가 깨어나서 일합니다.

**Watermark (모니터링 용)**
  
› _지금 '어디까지 처리했는가'를 추적하는 표시 — 처리가 밀렸는지 알 수 있다._
  
데이터 처리가 제때 안 되고 밀리면 대시보드가 오래된 정보를 보여줄 거예요. 워터마크를 보면 '아, Bronze 데이터는 어제 저녁까지만 들어왔는데 Silver는 어제 오후까지만 처리됐다 = 약 8시간 밀렸다'고 알 수 있습니다.

**CloudWatch Alarm (알람)**
  
› _문제 발생 시 '삐빅'하고 알려주는 시스템 — 이메일·SMS 등으로 운영자에게 통보._
  
예를 들어 'RDS의 저장공간이 2GB 미만이면 알려줘'라고 정합니다. 그러면 한 달에 한 번쯤 '저장공간 부족!' 알람이 와서 운영자가 '아, 지금 데이터 정리해야 하나' 하고 대응합니다. 마치 냉장고에 '식료품 없음' 알람이 뜨듯이.

**Data Quality (데이터 품질)**
  
› _지금 저장된 데이터가 얼마나 '좋은가' — Bronze는 몇 개, 검증 통과는 몇 개, quarantine은 몇 개._
  
매 시간 Validation이 끝나면, '총 신호 몇 개 중 pass 몇 개, fail 몇 개, error 몇 개'를 카운트해서 대시보드에 표시합니다. 만약 fail이 갑자기 많아지면 '어? 뭔가 문제다'고 알 수 있습니다. 마치 공장이 '불량률 5% → 15%'로 증가하면 '기계 점검해야 한다'고 알 수 있듯이.

### 7. 데이터 전송·인코딩 — 차량이 안전하게 보내는 방식

**mTLS (상호 TLS)**
  
› _차량과 서버가 '너 누니?'를 서로 확인하는 보안 통신._
  
https는 '서버가 진짜 구글인지 확인'하는 것(TLS). mTLS는 서버도 차량을 확인하고, 차량도 서버를 확인합니다. 마치 경찰이 '신분증 보여줘'라고 하듯이, 양쪽이 서로 신분(인증서)을 보여줍니다. 차량이 mTLS로 데이터를 보내니까, 가짜 차량이 데이터를 보낼 수 없습니다.

**Protobuf (프로토버퍼)**
  
› _데이터를 효율적으로 압축·직렬화하는 형식 — JSON보다 작고 빠름._
  
JSON은 텍스트라서 용량이 커요. Protobuf는 '속도_123, 배터리_85'를 마치 부호(암호)처럼 작은 바이트로 표현합니다. 차량 ↔ 서버 통신에는 작고 빠른 Protobuf를 쓰고, 분석가가 읽기는 쉬운 JSON으로 변환합니다.

