"""Generate architecture diagram PNGs + combined PDF for the guides.

Outputs (PNG 8종, docs/figures/):
- teslafleet_arch_overview.png    : main architecture (가이드 3절)
- teslafleet_network_basic.png    : network basic (가이드 2.4절)
- teslafleet_bronze_to_silver.png : Lakehouse Bronze→Validation→Silver
- teslafleet_full_architecture.png: 전체 구성(서빙+분석)
- teslafleet_overview_flow.png    : 전체 데이터 흐름(Kafka 허브)
- teslafleet_serving_path.png     : 실시간 서빙 경로(RDS)
- teslafleet_onboarding.png       : 차주 온보딩(OAuth)
- teslafleet_security_flow.png    : 보안·관리 구성
+ 합본 PDF 1종(docs/, 날짜 suffix — __main__의 pdf_path).

Style: clean boxes, color-coded zones, Korean labels via Apple SD Gothic Neo.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

# ----- Font -----
plt.rcParams["font.family"] = ["Apple SD Gothic Neo", "Apple SD Gothic Neo", "AppleGothic", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["pdf.fonttype"] = 42

# ----- Colors -----
C_VEHICLE = "#e8f4ff"
C_INGEST = "#dff2e1"     # data ingest zone (telemetry/kafka)
C_APP = "#fff4d6"        # application zone
C_STORE = "#ffe3d6"      # storage zone
C_USER = "#e8e8ff"       # browser/user
C_CDN = "#ddeaff"        # CloudFront
C_SEC = "#f0f0f3"        # security/management strip
EDGE = "#5b667a"
TEXT = "#1f2328"
ARROW = "#3b4554"


def box(ax, x, y, w, h, label, *, fill, label_color=TEXT, label_size=10.5, sub=None, sub_size=8.5, weight="bold"):
    """Rounded rectangle with centered label and optional sub-label."""
    p = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.012,rounding_size=0.02",
        linewidth=1.1, edgecolor=EDGE, facecolor=fill,
    )
    ax.add_patch(p)
    if sub:
        ax.text(x + w / 2, y + h * 0.62, label, ha="center", va="center",
                fontsize=label_size, color=label_color, fontweight=weight)
        ax.text(x + w / 2, y + h * 0.30, sub, ha="center", va="center",
                fontsize=sub_size, color="#555")
    else:
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
                fontsize=label_size, color=label_color, fontweight=weight)


def arrow(ax, x0, y0, x1, y1, *, label=None, label_off=(0, 0.05), color=ARROW, style="-|>", lw=1.4, ls="-"):
    a = FancyArrowPatch(
        (x0, y0), (x1, y1),
        arrowstyle=style, mutation_scale=14,
        linewidth=lw, color=color, linestyle=ls,
        shrinkA=2, shrinkB=2,
    )
    ax.add_patch(a)
    if label:
        mx, my = (x0 + x1) / 2 + label_off[0], (y0 + y1) / 2 + label_off[1]
        ax.text(mx, my, label, ha="center", va="center", fontsize=8.2,
                color="#2f3845",
                bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=0.92))


# =====================================================================
# 1) Main architecture overview
# =====================================================================
def make_overview(out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(11.8, 6.4), dpi=180)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 7.2)
    ax.axis("off")

    # ----- Row 1: 데이터 수집 (top) -----
    # Tesla Vehicle
    box(ax, 0.2, 5.4, 1.6, 1.1, "Tesla 차량", fill=C_VEHICLE, sub="(외부)")
    # Telemetry EC2
    box(ax, 3.0, 5.4, 2.4, 1.1, "telemetry EC2", fill=C_INGEST,
        sub="fleet-telemetry (Docker)\npublic subnet")
    # Kafka EC2
    box(ax, 6.4, 5.4, 2.4, 1.1, "kafka EC2", fill=C_INGEST,
        sub="Kafka 3.9 KRaft\n4 topics × 6 partitions")
    # mTLS arrow
    arrow(ax, 1.8, 5.95, 3.0, 5.95, label="mTLS 8443", label_off=(0, 0.18))
    arrow(ax, 5.4, 5.95, 6.4, 5.95, label="Kafka produce", label_off=(0, 0.18))

    # ----- Row 2: app EC2 컨테이너 영역 (center) -----
    box(ax, 9.4, 3.6, 2.4, 1.4, "", fill="#ffffff", weight="normal")
    ax.text(10.6, 4.85, "app EC2 (public subnet)", ha="center", va="center",
            fontsize=9.5, fontweight="bold", color=TEXT)
    # 5 containers inside
    cont_y = 3.8
    for i, name in enumerate(["nginx", "frontend", "backend", "kafka-consumer", "s3-archiver"]):
        # tight grid 2x3 (3 in top row, 2 in bottom)
        if i < 3:
            cx = 9.55 + 0.78 * i
            cy = 4.30
        else:
            cx = 9.75 + 0.78 * (i - 3)
            cy = 3.78
        rect = FancyBboxPatch((cx, cy), 0.72, 0.36,
                              boxstyle="round,pad=0.005,rounding_size=0.04",
                              linewidth=0.7, edgecolor=EDGE, facecolor=C_APP)
        ax.add_patch(rect)
        ax.text(cx + 0.36, cy + 0.18, name, ha="center", va="center",
                fontsize=7.4, color=TEXT)

    # CloudFront
    box(ax, 6.4, 3.6, 2.4, 1.1, "CloudFront", fill=C_CDN,
        sub="+ ACM cert + Route53")

    # Owner browser
    box(ax, 3.0, 3.6, 2.4, 1.1, "차주 브라우저", fill=C_USER, sub="(외부)")

    # arrows row 2
    arrow(ax, 5.4, 4.15, 6.4, 4.15, label="HTTPS", label_off=(0, 0.18))
    arrow(ax, 8.8, 4.15, 9.4, 4.15, label="HTTPS", label_off=(0, 0.18))

    # Kafka → kafka-consumer (vertical down from kafka EC2 into app EC2)
    arrow(ax, 7.6, 5.40, 10.5, 4.66, label=None)

    # ----- Row 3: storage (bottom) -----
    box(ax, 8.0, 1.5, 2.0, 1.1, "RDS PostgreSQL 16", fill=C_STORE,
        sub="(private subnet)", sub_size=8)
    box(ax, 10.4, 1.5, 1.5, 1.1, "S3 raw bucket", fill=C_STORE,
        sub="(AWS managed)", sub_size=8)

    # app EC2 → RDS / S3
    arrow(ax, 10.2, 3.6, 9.0, 2.6)
    arrow(ax, 11.0, 3.6, 11.15, 2.6)

    # ----- Row 4: security/management strip (bottom) -----
    # v1.6.1: 6항목(3행) — strip 높이 확대.
    strip = mpatches.FancyBboxPatch((0.2, 0.1), 11.6, 1.38,
                                     boxstyle="round,pad=0.012,rounding_size=0.02",
                                     linewidth=0.9, edgecolor="#bcc1c8", facecolor=C_SEC)
    ax.add_patch(strip)
    ax.text(0.5, 1.32, "보안/관리", fontsize=10, fontweight="bold", color=TEXT)

    sec_items = [
        "Secrets Manager  ⇄  KMS  ⇄  app EC2  (envelope encryption)",
        "RDS rotation Lambda (SAR)  →  RDS ALTER USER 30일마다",
        "VPC Interface Endpoint (secretsmanager)  ←  private subnet egress",
        "SNS topic  ←  telemetry EC2 cron (cert 만료 알림)",
        "app EC2 :80  ←  CloudFront origin-facing PL only  (직접 IP 차단)",
        "계정 로그인(tf_account 세션) — admin/manager  ·  onboard  세션쿠키(IDOR 차단)",
    ]
    for i, t in enumerate(sec_items):
        col = i % 2
        row = i // 2
        ax.text(0.55 + col * 5.6, 1.06 - row * 0.30, "•  " + t, fontsize=8.4, color=TEXT)

    # ----- Title -----
    ax.text(6.0, 6.95, "TeslaFleet AWS 인프라 구조", fontsize=14, fontweight="bold",
            color=TEXT, ha="center")

    # ----- Legend -----
    legend_items = [
        (C_VEHICLE, "외부 (차량/브라우저)"),
        (C_INGEST, "데이터 수집"),
        (C_CDN, "CDN/엣지"),
        (C_APP, "애플리케이션"),
        (C_STORE, "저장소"),
        (C_SEC, "보안/관리"),
    ]
    lx = 0.2
    for color, label in legend_items:
        ax.add_patch(mpatches.Rectangle((lx, 6.62), 0.22, 0.18, facecolor=color,
                                         edgecolor=EDGE, linewidth=0.6))
        ax.text(lx + 0.27, 6.71, label, fontsize=7.8, va="center", color=TEXT)
        lx += 1.65

    plt.tight_layout()
    plt.savefig(out_path, dpi=180, bbox_inches="tight",
                facecolor="white", pad_inches=0.15)
    plt.close(fig)


# =====================================================================
# 2) Network basics (2.4절) — simple inline
# =====================================================================
def make_network_basic(out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(8.0, 3.6), dpi=180)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")

    # 인터넷
    box(ax, 0.2, 1.6, 1.8, 0.9, "인터넷", fill="#fff4d6")
    # IGW
    box(ax, 2.4, 1.6, 1.6, 0.9, "Internet\nGateway (IGW)", fill=C_CDN, label_size=9.5)
    # Public subnet
    box(ax, 4.4, 2.4, 2.6, 1.0, "Public Subnet", fill="#dff2e1",
        sub="10.0.0.0/24  ·  인터넷 직접 접근 가능", sub_size=7.6)
    # Private subnet
    box(ax, 4.4, 0.7, 2.6, 1.0, "Private Subnet", fill="#ffe3d6",
        sub="10.0.10.0/24  ·  내부 통신만", sub_size=7.6)
    # VPC label envelope
    vpc = mpatches.FancyBboxPatch((4.2, 0.5), 5.5, 3.1,
                                   boxstyle="round,pad=0.012,rounding_size=0.04",
                                   linewidth=1.0, edgecolor="#8092a6", facecolor="none", linestyle="--")
    ax.add_patch(vpc)
    ax.text(9.6, 3.45, "VPC  10.0.0.0/16", fontsize=8.4, ha="right", va="top", color="#5b667a")

    # arrows
    arrow(ax, 2.0, 2.05, 2.4, 2.05)
    arrow(ax, 4.0, 2.05, 4.4, 2.90, label_off=(0, 0.18))
    arrow(ax, 5.7, 2.40, 5.7, 1.70, label="route table", label_off=(0.85, 0))

    ax.text(5.0, 3.75, "네트워크 기초 (2.4절)", fontsize=11, fontweight="bold",
            color=TEXT, ha="center")

    plt.tight_layout()
    plt.savefig(out_path, dpi=180, bbox_inches="tight",
                facecolor="white", pad_inches=0.12)
    plt.close(fig)


# =====================================================================
# 3) Iceberg Bronze 이후 — Contract Validation → Silver 데이터플로우
# =====================================================================
def make_bronze_to_silver(out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(13.5, 5.0), dpi=180)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 5.5)
    ax.axis("off")

    c_ice = "#dde8f5"     # Iceberg table
    c_glue = "#ffe9c7"    # Glue Spark job
    c_view = "#e3f1e0"    # Athena view
    c_silver = "#e8e0f5"  # Silver

    # main row (좌→우): Bronze → Validation → result → current → valid → Silver job → signals
    nodes = [
        (0.2, "Bronze Raw", c_ice, "telemetry_raw\nIceberg 5-field"),
        (2.15, "Glue\nValidation", c_glue, "scheduler 1h(:00)\nENABLED"),
        (4.1, "validation_result", c_ice, "Iceberg · Glue 단독"),
        (6.25, "current_v", c_view, "offset별 최신"),
        (8.2, "valid_v", c_view, "status=pass"),
        (10.15, "Glue\nBronze→Silver", c_glue, "scheduler 1h(:30)\nENABLED"),
        (12.1, "telemetry_signals", c_silver, "Silver · long\n신호별 1행"),
    ]
    w, h, y = 1.78, 1.1, 3.0
    for i, (x, lab, c, sub) in enumerate(nodes):
        box(ax, x, y, w, h, lab, fill=c, sub=sub, sub_size=6.6, label_size=8.3)
        if i > 0:
            arrow(ax, nodes[i - 1][0] + w, y + h / 2, x, y + h / 2)

    # current_v → quarantine / pending (분기, 아래)
    box(ax, 5.4, 1.2, 1.78, 0.8, "quarantine_v", fill="#fbe0e0", sub="status=fail", sub_size=6.6, label_size=8)
    box(ax, 7.4, 1.2, 1.78, 0.8, "pending_v", fill="#f0f0f3", sub="미검증", sub_size=6.6, label_size=8)
    arrow(ax, 6.9, 3.0, 6.3, 2.0)
    arrow(ax, 7.2, 3.0, 8.3, 2.0)

    ax.text(7.0, 5.05, "Iceberg Bronze 이후 — Contract Validation → Silver", fontsize=12.5,
            fontweight="bold", color=TEXT, ha="center")
    ax.text(7.0, 0.55, "validation_result · telemetry_signals 는 Glue 단독 생성·관리 (Athena DDL+Spark write 혼용 금지)",
            fontsize=7.4, color="#555", ha="center")

    plt.tight_layout()
    plt.savefig(out_path, dpi=180, bbox_inches="tight", facecolor="white", pad_inches=0.15)
    plt.close(fig)


# =====================================================================
# Swimlane 헬퍼 (5/29 참고본 스타일 — 컬럼 레인 + 컬러바 박스 + 번호뱃지 + 범례)
# 라이트 테마·가독성 우선. 내용 정확성은 wljses83j 아키텍처 매핑(코드 검증) 기준.
# =====================================================================
# 박스 종류별 색(좌측 컬러바 + 옅은 배경) — 의미를 색으로 구분.
ZONE = {
    "ext":   ("#3b82f6", "#eff6ff"),  # 외부(차량/브라우저/Tesla)
    "edge":  ("#06b6d4", "#ecfeff"),  # 엣지(CloudFront/nginx)
    "comp":  ("#f59e0b", "#fff7ed"),  # 컴퓨트(EC2/컨테이너)
    "store": ("#a855f7", "#faf5ff"),  # 저장소(RDS/S3)
    "lake":  ("#10b981", "#ecfdf5"),  # Lakehouse(Glue/Iceberg)
    "sec":   ("#ef4444", "#fef2f2"),  # 보안/관리(KMS/Secrets/SNS)
}


def lane_box(ax, x, y, w, h, title, lines, zone):
    """좌측 컬러바 + 제목 + 본문 여러 줄 박스 (swimlane 노드)."""
    bar, bg = ZONE[zone]
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.03",
        linewidth=1.0, edgecolor="#cbd2da", facecolor=bg, zorder=2))
    # 좌측 컬러 바
    ax.add_patch(mpatches.Rectangle((x, y), 0.08, h, facecolor=bar, edgecolor="none", zorder=3))
    ax.text(x + 0.22, y + h - 0.26, title, ha="left", va="top",
            fontsize=9.6, fontweight="bold", color="#1f2328", zorder=4)
    for i, ln in enumerate(lines):
        ax.text(x + 0.22, y + h - 0.56 - i * 0.30, ln, ha="left", va="top",
                fontsize=7.7, color="#444", zorder=4)


def badge(ax, x, y, n, color="#f59e0b"):
    """번호 뱃지 (흐름 순서)."""
    ax.add_patch(mpatches.Circle((x, y), 0.17, facecolor=color, edgecolor="white", linewidth=1.4, zorder=6))
    ax.text(x, y, str(n), ha="center", va="center", fontsize=8.5, fontweight="bold", color="white", zorder=7)


def flow_arrow(ax, x0, y0, x1, y1, *, color="#6b7686", lw=1.6, ls="-", rad=0.0):
    cs = f"arc3,rad={rad}" if rad else None
    ax.add_patch(FancyArrowPatch(
        (x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=15,
        linewidth=lw, color=color, linestyle=ls, shrinkA=3, shrinkB=3,
        connectionstyle=cs, zorder=5))


def swimlane_columns(ax, cols, top, bottom):
    """컬럼 헤더 + 세로 구분선. cols=[(x_center, label), ...]."""
    for i, (cx, lab) in enumerate(cols):
        ax.text(cx, top + 0.18, lab, ha="center", va="bottom",
                fontsize=9.5, fontweight="bold", color="#5b667a")
        if i > 0:
            xline = (cols[i - 1][0] + cx) / 2
            ax.plot([xline, xline], [bottom, top], color="#e2e6eb", lw=1.0, zorder=1)


def legend_flows(ax, x, y, items, cols=2, dy=0.34, dx=6.4):
    """하단 흐름 범례 — 번호뱃지 + 설명."""
    for i, (n, txt, color) in enumerate(items):
        col = i % cols
        row = i // cols
        bx = x + col * dx
        by = y - row * dy
        badge(ax, bx, by, n, color=color)
        ax.text(bx + 0.32, by, txt, ha="left", va="center", fontsize=8.2, color="#333")


# =====================================================================
# 재설계 원칙(2026-06): 각 도식은 한 가지 이야기 · 한 방향 흐름(교차/관통 0).
# Kafka를 허브로 보고 수집/실시간서빙/분석(Lakehouse)/온보딩/보안을 분리.
# 내용은 아키텍처 매핑(wljses83j, 코드 검증) 기준.
# =====================================================================

def hbox(ax, x, y, w, h, title, lines, zone, *, ts=10.0, ls=7.9):
    """가로 흐름용 박스(좌측 컬러바 + 제목 + 본문). lane_box와 동일 스타일, 폰트만 조정."""
    bar, bg = ZONE[zone]
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.04",
        linewidth=1.0, edgecolor="#c4ccd4", facecolor=bg, zorder=2))
    ax.add_patch(mpatches.Rectangle((x, y), 0.07, h, facecolor=bar, edgecolor="none", zorder=3))
    ax.text(x + w / 2, y + h - 0.30, title, ha="center", va="top",
            fontsize=ts, fontweight="bold", color="#1f2328", zorder=4)
    for i, ln in enumerate(lines):
        ax.text(x + w / 2, y + h - 0.62 - i * 0.30, ln, ha="center", va="top",
                fontsize=ls, color="#4a4a4a", zorder=4)


def step_arrow(ax, x0, y0, x1, y1, *, n=None, label=None, color="#5b667a", lw=1.8, rad=0.0, lab_dy=0.26, badge_at=0.5):
    """단계 화살표 — 직선 우선, 번호뱃지는 중앙, 라벨은 위."""
    cs = f"arc3,rad={rad}" if rad else None
    ax.add_patch(FancyArrowPatch(
        (x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=16,
        linewidth=lw, color=color, linestyle="-", shrinkA=4, shrinkB=4,
        connectionstyle=cs, zorder=4))
    mx = x0 + (x1 - x0) * badge_at
    my = y0 + (y1 - y0) * badge_at
    if label:
        ax.text(mx, my + lab_dy, label, ha="center", va="bottom", fontsize=7.8, color="#33404e",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.95), zorder=5)
    if n is not None:
        badge(ax, mx, my, n, color=color)


# =====================================================================
# A) 전체 데이터 흐름 한눈에 — Kafka 허브에서 2갈래(서빙/분석)
# =====================================================================
def make_overview_flow(out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(13.8, 10.2), dpi=160)
    ax.set_xlim(0, 13.8); ax.set_ylim(0, 10.4); ax.axis("off")
    ax.text(6.9, 10.05, "TeslaFleet 전체 데이터 흐름 (v1.7.0)", fontsize=15.5, fontweight="bold", color=TEXT, ha="center")
    ax.text(6.9, 9.6, "차량 텔레메트리는 Kafka(허브)에 모인 뒤, ‘실시간 서빙(RDS)’과 ‘분석(Lakehouse)’ 두 갈래로 갈라집니다.",
            fontsize=8.8, color="#666", ha="center")

    W, H = 3.1, 1.35
    # 수집 (상단 가로): 차량 → telemetry → Kafka — 박스 설명 보강
    hbox(ax, 0.5, 7.5, W, H, "Tesla 차량", ["주행 신호를 보내는 출발점", "mTLS:8443 · Protobuf"], "ext")
    hbox(ax, 4.4, 7.5, W, H, "telemetry EC2", ["수신 서버(fleet-telemetry, Go)", "Protobuf → JSON 변환"], "comp")
    hbox(ax, 8.3, 7.5, 4.7, H, "Kafka (메시지 허브)", ["모든 메시지가 모이는 중앙 큐", "4 topics × 6 part · 30일 보존"], "comp")
    step_arrow(ax, 3.6, 8.17, 4.4, 8.17, n=1, label="mTLS 스트림", color="#3b82f6")
    step_arrow(ax, 7.5, 8.17, 8.3, 8.17, n=2, label="produce", color="#f59e0b")

    # Kafka 허브에서 아래로 2갈래 — 박스 상단으로 정확히 도착(관통 회피)
    step_arrow(ax, 9.0, 7.5, 2.0, 6.35, n=3, label="consume (서빙)", color="#a855f7", rad=0.10, badge_at=0.62)
    step_arrow(ax, 10.6, 7.5, 1.64, 4.05, n=6, label="consume (분석)", color="#10b981", rad=0.10, badge_at=0.72)

    # 서빙 갈래 (중단)
    ax.text(0.5, 6.62, "─ 실시간 서빙 (대시보드) ─", fontsize=9.4, fontweight="bold", color="#a855f7")
    hbox(ax, 0.5, 5.1, 3.0, H, "kafka-consumer", ["메시지를 DB에 적재", "batch INSERT · carry-forward"], "comp")
    hbox(ax, 4.4, 5.1, 2.9, H, "RDS PostgreSQL", ["가공된 현재 상태(빠른 조회)", "telemetry_events · vehicles"], "store")
    hbox(ax, 8.3, 5.1, 4.7, H, "backend ← nginx ← CloudFront ← 차주", ["대시보드 서빙(조회 API+캐시)", "차주가 보는 화면(sphere)"], "edge")
    step_arrow(ax, 3.5, 5.77, 4.4, 5.77, n=4, label="bulk INSERT", color="#a855f7")
    step_arrow(ax, 8.3, 5.77, 7.3, 5.77, n=5, label="SQL 조회", color="#06b6d4")

    # 분석 갈래 (하단)
    ax.text(0.5, 4.25, "─ 분석 Lakehouse (Iceberg) ─", fontsize=9.4, fontweight="bold", color="#10b981")
    wL = 2.28
    lake = [
        (0.5, "s3-archiver", ["원본 보관 + 변환", "raw.v1 publish"], "comp"),
        (3.05, "Kafka Connect", ["Iceberg에 적재", "→ Glue Catalog"], "lake"),
        (5.6, "Bronze", ["원본 보존층", "telemetry_raw"], "lake"),
        (8.15, "Validation", ["검증 게이트", "valid_v · 매시 :00"], "lake"),
        (10.7, "Silver", ["분석용 정제층", "신호별 1행 · 매시 :30"], "lake"),
    ]
    for i, (x, t, ls_, z) in enumerate(lake):
        hbox(ax, x, 2.75, wL, H, t, ls_, z, ts=9.4, ls=7.3)
        if i > 0:
            step_arrow(ax, lake[i - 1][0] + wL, 3.42, x, 3.42, n=(7 if i == 1 else None), color="#10b981")

    # ── 하단: 번호 태그 흐름 설명 ──
    ax.add_patch(mpatches.FancyBboxPatch((0.4, 0.25), 13.0, 1.85, boxstyle="round,pad=0.01,rounding_size=0.02",
                 linewidth=0.9, edgecolor="#cdd3da", facecolor="#fafbfc", zorder=1))
    ax.text(0.65, 1.92, "흐름 설명", fontsize=9.6, fontweight="bold", color="#5b667a")
    legend_flows(ax, 0.8, 1.55, [
        (1, "차량 → telemetry EC2 (mTLS 8443, 암호화 스트림)", "#3b82f6"),
        (2, "telemetry → Kafka 적재 (Protobuf→JSON, produce)", "#f59e0b"),
        (3, "Kafka → kafka-consumer (서빙용으로 읽기)", "#a855f7"),
        (4, "consumer → RDS 적재 (대시보드용 가공 상태)", "#a855f7"),
        (5, "backend → RDS 조회 (차주 대시보드 응답)", "#06b6d4"),
        (6, "Kafka → s3-archiver (분석용으로 읽기)", "#10b981"),
        (7, "Connect → Iceberg Bronze→Validation→Silver (단계 정제)", "#10b981"),
    ], cols=2, dx=6.7, dy=0.36)

    plt.savefig(out_path, dpi=160, bbox_inches="tight", facecolor="white", pad_inches=0.25)
    plt.close(fig)


# =====================================================================
# B) 실시간 서빙 경로 — 적재(왼쪽) + 조회(오른쪽)가 RDS에서 만남
# =====================================================================
def make_serving_path(out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(14.0, 5.2), dpi=160)
    ax.set_xlim(0, 14); ax.set_ylim(0, 5.4); ax.axis("off")
    ax.text(7.0, 5.05, "실시간 서빙 경로 — RDS가 ‘적재’와 ‘조회’의 공유 상태", fontsize=14.5, fontweight="bold", color=TEXT, ha="center")
    ax.text(7.0, 4.55, "왼쪽: Kafka→consumer가 데이터를 적재 ·  오른쪽: 차주 대시보드 요청이 backend를 거쳐 조회. 둘 다 RDS에서 만납니다.",
            fontsize=8.6, color="#666", ha="center")

    W, H, y = 2.35, 1.5, 1.9
    # 왼쪽(적재): Kafka → kafka-consumer → RDS(중앙)
    hbox(ax, 0.3, y, W, H, "Kafka", ["tesla_V topic", "6 partitions"], "comp")
    hbox(ax, 3.1, y, W, H, "kafka-consumer", ["batch INSERT", "VIN cache + carry-fwd"], "comp")
    hbox(ax, 5.85, y, 2.3, H, "RDS PostgreSQL", ["telemetry_events", "vehicles · alerts"], "store")
    # 오른쪽(조회): RDS ← backend ← nginx/CloudFront ← 차주
    hbox(ax, 8.7, y, W, H, "backend (FastAPI)", ["조회 API + 60s 캐시", "계정 세션(admin/manager)"], "comp")
    hbox(ax, 11.5, y, W, H, "차주 브라우저", ["CloudFront→nginx", "SPA 대시보드"], "ext")

    step_arrow(ax, 2.65, y + H / 2, 3.1, y + H / 2, n=1, color="#f59e0b")
    step_arrow(ax, 5.45, y + H / 2, 5.85, y + H / 2, n=2, label="bulk INSERT", color="#a855f7")
    step_arrow(ax, 8.7, y + H / 2, 8.15, y + H / 2, n=3, label="SQL 조회", color="#06b6d4")
    step_arrow(ax, 11.5, y + H / 2, 11.05, y + H / 2, n=4, label="HTTPS", color="#3b82f6")

    legend_flows(ax, 0.4, 0.85, [
        (1, "fleet-telemetry → Kafka → consumer (수집)", "#f59e0b"),
        (2, "consumer → RDS 적재 (process_v_batch_optimized)", "#a855f7"),
        (3, "backend → RDS 조회 (대시보드 API, 캐시)", "#06b6d4"),
        (4, "차주 → CloudFront → nginx → backend (HTTPS)", "#3b82f6"),
    ], cols=2, dx=7.0)

    plt.savefig(out_path, dpi=160, bbox_inches="tight", facecolor="white", pad_inches=0.25)
    plt.close(fig)


# =====================================================================
# C) 차주 온보딩(OAuth) — 로그인 → 토큰 → 차량 등록 → 수집 시작
# =====================================================================
def make_onboarding(out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(14.0, 6.4), dpi=160)
    ax.set_xlim(0, 14); ax.set_ylim(0, 6.6); ax.axis("off")
    ax.text(7.0, 6.25, "차주 온보딩 (OAuth) — 계정 연결 → 차량 등록 → 텔레메트리 수집 시작", fontsize=14, fontweight="bold", color=TEXT, ha="center")

    W, H, y = 2.5, 1.4, 3.6
    steps = [
        (0.3, "차주 로그인", ["우리 서비스에서", "Tesla 로그인 시작"], "ext"),
        (3.0, "Tesla 인증", ["auth.tesla.com 동의", "권한 5개 부여"], "ext"),
        (5.7, "callback", ["토큰 받아 저장", "세션쿠키 발급"], "comp"),
        (8.4, "차량 등록", ["fleet_telemetry_config", "차량에 전송"], "comp"),
        (11.1, "수집 시작", ["차량이 텔레메트리", "전송 → Kafka"], "store"),
    ]
    arrow_labels = ["로그인", "인가코드", "토큰교환", "config push"]
    for i, (x, t, ls_, z) in enumerate(steps):
        hbox(ax, x, y, W, H, t, ls_, z, ts=10.0, ls=7.7)
        if i > 0:
            step_arrow(ax, steps[i - 1][0] + W, y + H / 2, x, y + H / 2, n=i,
                       label=arrow_labels[i - 1], color="#06b6d4", lab_dy=0.22)

    # 번호 태그 설명 범례
    ax.add_patch(mpatches.FancyBboxPatch((0.3, 1.7), 13.4, 1.05, boxstyle="round,pad=0.01,rounding_size=0.02",
                 linewidth=0.9, edgecolor="#cdd3da", facecolor="#fafbfc", zorder=1))
    ax.text(0.55, 2.58, "단계 설명", fontsize=9.4, fontweight="bold", color="#5b667a")
    legend_flows(ax, 0.7, 2.25, [
        (1, "차주가 우리 서비스 → Tesla 로그인 페이지로 이동", "#06b6d4"),
        (2, "로그인·동의 후 인가코드를 callback으로 받음", "#06b6d4"),
        (3, "인가코드 → 토큰 교환(fleet-auth) + DB 저장", "#06b6d4"),
        (4, "차량에 텔레메트리 설정 push → 수집 개시", "#06b6d4"),
    ], cols=2, dx=6.8, dy=0.4)

    ax.text(7.0, 1.18,
            "토큰 교환 host = fleet-auth.prd.vn.cloud.tesla.com (authorize는 auth.tesla.com 유지) · onboard 인증 = HMAC 서명 세션쿠키(tf_onboard_owner, IDOR 차단)",
            fontsize=7.8, color="#555", ha="center")
    ax.text(7.0, 0.78,
            "register 시 prefer_typed=true로 신호 oneof 전송 · 412/needs_pairing이면 virtual key 페어링 deeplink 안내",
            fontsize=7.8, color="#555", ha="center")

    plt.savefig(out_path, dpi=160, bbox_inches="tight", facecolor="white", pad_inches=0.25)
    plt.close(fig)


# =====================================================================
# D) 보안 · 관리 — 영역별 그룹(교차 없는 묶음 보기)
# =====================================================================
def make_security_flow(out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(14.0, 7.6), dpi=160)
    ax.set_xlim(0, 14); ax.set_ylim(0, 7.8); ax.axis("off")
    ax.text(7.0, 7.45, "보안 · 관리 구성 (v1.7.0)", fontsize=15, fontweight="bold", color=TEXT, ha="center")

    def group(x, y, w, h, title):
        ax.add_patch(mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.02",
                     linewidth=1.0, edgecolor="#b9c0c9", facecolor="#fafbfc", zorder=1))
        ax.text(x + 0.2, y + h - 0.05, title, ha="left", va="top", fontsize=10, fontweight="bold", color="#5b667a")

    W, H = 2.7, 1.1
    # 그룹1: 비밀/암호화 (왼쪽 위)
    group(0.3, 3.9, 6.6, 3.4, "① 비밀 관리 · 토큰 암호화")
    hbox(ax, 0.6, 5.7, W, H, "backend (startup)", ["_inject_db_url_from_secret", "token_crypto envelope"], "comp")
    hbox(ax, 4.0, 5.7, W, H, "Secrets Manager", ["rds/credentials(30d)", "tesla-client·telemetry/*"], "store")
    hbox(ax, 0.6, 4.2, W, H, "VPC Interface EP", ["secretsmanager(private)", "+ S3 Gateway EP"], "edge")
    hbox(ax, 4.0, 4.2, W, H, "KMS token-envelope", ["AES-256-GCM DEK", "vehicle_owner_tokens"], "store")
    step_arrow(ax, 3.3, 6.25, 4.0, 6.25, n=1, color="#06b6d4")
    step_arrow(ax, 3.3, 4.75, 4.0, 4.75, n=2, color="#a855f7")

    # 그룹2: RDS 자격 자동 교체 (오른쪽 위)
    group(7.1, 3.9, 6.6, 3.4, "② RDS 비밀번호 자동 교체")
    hbox(ax, 7.4, 5.7, W, H, "rotation Lambda(SAR)", ["SingleUser 30일", "create→set→test→finish"], "lake")
    hbox(ax, 10.8, 5.7, W, H, "Secrets Manager", ["rds/credentials", "새 password PUT"], "store")
    hbox(ax, 9.1, 4.2, W, H, "RDS PostgreSQL", ["db.t4g.small(private)", "ALTER USER 30일"], "store")
    step_arrow(ax, 10.1, 6.25, 10.8, 6.25, n=3, label="PUT", color="#10b981")
    step_arrow(ax, 9.3, 5.7, 10.1, 5.3, n=4, label="ALTER USER", color="#10b981", lab_dy=0.12)

    # 그룹3: 네트워크·앱 인증 (왼쪽 아래)
    group(0.3, 0.5, 6.6, 3.3, "③ 네트워크 · 앱 인증")
    hbox(ax, 0.6, 2.4, W, H, "EC2 app :80", ["CloudFront origin", "prefix-list only(직접IP 차단)"], "sec")
    hbox(ax, 4.0, 2.4, W, H, "계정 로그인(0041)", ["tf_account 세션 쿠키", "admin/manager 스코프"], "sec")
    hbox(ax, 0.6, 1.0, W, H, "onboard 세션쿠키", ["tf_onboard_owner HMAC", "owner_id 쿼리 불신"], "sec")
    hbox(ax, 4.0, 1.0, W, H, "nginx", ["rate limit · default 444", "(Basic auth 제거 v1.7.0)"], "edge")

    # 그룹4: 인증서 만료 알림 (오른쪽 아래)
    group(7.1, 0.5, 6.6, 3.3, "④ 인증서 만료 모니터링")
    hbox(ax, 7.4, 2.4, W, H, "telemetry cron", ["check-cert-expiry.sh", "06:00 KST 매일"], "comp")
    hbox(ax, 10.8, 2.4, W, H, "SNS cert-alerts", ["30/14/7d 임계", "→ email 구독"], "sec")
    hbox(ax, 9.1, 1.0, W, H, "mTLS 인증서", ["자체 CA/server", "Secrets telemetry/*"], "store")
    step_arrow(ax, 10.1, 3.0, 10.8, 3.0, n=5, label="만료 임박", color="#ef4444")

    plt.savefig(out_path, dpi=160, bbox_inches="tight", facecolor="white", pad_inches=0.25)
    plt.close(fig)


# =====================================================================
# 4) 전체 서비스 아키텍처 (수집 → 운영 + Lakehouse) — end-to-end
# =====================================================================
def make_full_architecture(out_path: str) -> None:
    fig, ax = plt.subplots(figsize=(16.0, 9.0), dpi=160)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9.3)
    ax.axis("off")

    # swimlane bands
    for by, bh, blab, bc in [
        (6.6, 2.2, "①  데이터 수집", "#eef6ee"),
        (3.7, 2.5, "②  운영 / 애플리케이션 (서빙)", "#fff8e8"),
        (0.4, 2.9, "③  Lakehouse (Iceberg · 분석)", "#eef2fb"),
    ]:
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.15, by), 15.7, bh,
            boxstyle="round,pad=0.01,rounding_size=0.02",
            linewidth=0.8, edgecolor="#c8ccd2", facecolor=bc))
        ax.text(0.4, by + bh - 0.22, blab, fontsize=10, fontweight="bold", color="#5b667a", va="top")

    # ① 수집 (y=6.95)
    box(ax, 0.5, 6.95, 1.9, 1.0, "Tesla 차량", fill=C_VEHICLE, sub="(외부)")
    box(ax, 3.0, 6.95, 2.2, 1.0, "telemetry EC2", fill=C_INGEST, sub="fleet-telemetry · mTLS:8443", sub_size=7.4)
    box(ax, 6.0, 6.95, 2.2, 1.0, "Kafka EC2", fill=C_INGEST, sub="3.9 KRaft · 4 topics + raw.v1", sub_size=7.4)
    arrow(ax, 2.4, 7.45, 3.0, 7.45, label="mTLS")
    arrow(ax, 5.2, 7.45, 6.0, 7.45, label="produce")

    # ② 운영 (y=4.5)
    box(ax, 0.5, 4.5, 1.9, 1.0, "차주 브라우저", fill=C_USER, sub="(외부)")
    box(ax, 3.0, 4.5, 1.9, 1.0, "CloudFront", fill=C_CDN, sub="ACM+Route53", sub_size=7.4)
    box(ax, 5.5, 4.5, 2.7, 1.0, "app EC2", fill=C_APP, sub="nginx·frontend·backend\nkafka-consumer·s3-archiver", sub_size=7.0)
    box(ax, 9.0, 4.5, 1.9, 1.0, "RDS PG16", fill=C_STORE, sub="telemetry_events", sub_size=7.4)
    box(ax, 11.5, 4.5, 1.9, 1.0, "S3 bucket", fill=C_STORE, sub="topics/ (archiver)\nwarehouse/ (Iceberg)", sub_size=6.8)
    arrow(ax, 2.4, 5.0, 3.0, 5.0, label="HTTPS")
    arrow(ax, 4.9, 5.0, 5.5, 5.0, label="origin PL only", label_off=(0, 0.2))
    arrow(ax, 8.2, 5.0, 9.0, 5.0, label="SQL")
    # app(s3-archiver) → S3 topics/  (RDS 위로 곡선 우회해 박스 라벨 침범 방지)
    a = FancyArrowPatch((8.2, 5.35), (11.5, 5.35), connectionstyle="arc3,rad=-0.28",
                        arrowstyle="-|>", mutation_scale=14, linewidth=1.4, color="#9aa3b0")
    ax.add_patch(a)
    ax.text(9.9, 6.05, "archive", ha="center", va="center", fontsize=8.2, color="#2f3845",
            bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none", alpha=0.92))
    # Kafka → app (수집 → 운영)
    arrow(ax, 7.0, 6.95, 6.85, 5.5, label="consume", label_off=(0.55, 0))

    # ③ lakehouse (y=1.45)
    yL = 1.45
    lake = [
        (2.7, "Kafka Connect", C_APP, "Iceberg Sink"),
        (4.85, "Bronze", "#dde8f5", "telemetry_raw"),
        (7.0, "Glue\nValidation", "#ffe9c7", "1h(:00) ENABLED"),
        (9.15, "valid_v", "#e3f1e0", "pass · 게이트"),
        (11.3, "Glue\nSilver", "#ffe9c7", "1h(:30) ENABLED"),
        (13.45, "telemetry_signals", "#e8e0f5", "long · 분석"),
    ]
    wL, hL = 1.9, 1.0
    for i, (x, lab, c, sub) in enumerate(lake):
        box(ax, x, yL, wL, hL, lab, fill=c, sub=sub, sub_size=6.6, label_size=8)
        if i > 0:
            arrow(ax, lake[i - 1][0] + wL, yL + hL / 2, x, yL + hL / 2)
    # app(s3-archiver) → telemetry.raw.v1 → Connect (운영 → lakehouse 진입)
    arrow(ax, 6.0, 4.5, 3.65, 2.45, label="raw.v1", color="#7a8496", label_off=(0.5, 0))

    ax.text(8.0, 9.05, "TeslaFleet 전체 서비스 아키텍처", fontsize=15, fontweight="bold", color=TEXT, ha="center")
    ax.text(8.0, 0.16,
            "수집(Kafka) → 운영(kafka-consumer→RDS, CloudFront 서빙) + Lakehouse(s3-archiver→Connect→Bronze→Validation→Silver). Iceberg 테이블은 Glue 단독 관리.",
            fontsize=7.6, color="#555", ha="center")

    plt.savefig(out_path, dpi=160, bbox_inches="tight", facecolor="white", pad_inches=0.2)
    plt.close(fig)


# =====================================================================
# 5) 4개 도식 합본 PDF (docs/teslafleet_diagrams_<date>.pdf 교체용)
# =====================================================================
def make_combined_pdf(out_path: str, png_dir: str) -> None:
    """make_* 5종 PNG(png_dir)를 1 PDF(5페이지)로 합본.

    페이지 순서: 전체 데이터 흐름 → 실시간 서빙 경로 → Bronze→Silver → 온보딩 → 보안·관리.
    """
    import os

    import matplotlib.image as mpimg
    from matplotlib.backends.backend_pdf import PdfPages

    pngs = [
        "teslafleet_overview_flow.png",     # 1) 전체 데이터 흐름 한눈에 (Kafka 허브)
        "teslafleet_serving_path.png",      # 2) 실시간 서빙 경로 (RDS 중심)
        "teslafleet_bronze_to_silver.png",  # 3) Lakehouse: Bronze→Validation→Silver
        "teslafleet_onboarding.png",        # 4) 차주 온보딩 (OAuth)
        "teslafleet_security_flow.png",     # 5) 보안·관리 구성
    ]
    with PdfPages(out_path) as pdf:
        for name in pngs:
            img = mpimg.imread(os.path.join(png_dir, name))
            ih, iw = img.shape[0], img.shape[1]
            figp, axp = plt.subplots(figsize=(iw / 180, ih / 180), dpi=180)
            axp.imshow(img)
            axp.axis("off")
            pdf.savefig(figp, bbox_inches="tight", pad_inches=0.05)
            plt.close(figp)


if __name__ == "__main__":
    import os
    out_dir = os.path.dirname(os.path.abspath(__file__))
    make_overview(os.path.join(out_dir, "teslafleet_arch_overview.png"))
    make_network_basic(os.path.join(out_dir, "teslafleet_network_basic.png"))
    make_bronze_to_silver(os.path.join(out_dir, "teslafleet_bronze_to_silver.png"))
    make_full_architecture(os.path.join(out_dir, "teslafleet_full_architecture.png"))
    make_overview_flow(os.path.join(out_dir, "teslafleet_overview_flow.png"))
    make_serving_path(os.path.join(out_dir, "teslafleet_serving_path.png"))
    make_onboarding(os.path.join(out_dir, "teslafleet_onboarding.png"))
    make_security_flow(os.path.join(out_dir, "teslafleet_security_flow.png"))
    # 합본 PDF — docs/ 상위로 출력(이전 날짜본은 git에서 정리)
    docs_dir = os.path.dirname(out_dir)
    pdf_path = os.path.join(docs_dir, "teslafleet_diagrams_2026-06-11.pdf")
    make_combined_pdf(pdf_path, out_dir)
    print("generated:")
    for f in ("teslafleet_arch_overview.png", "teslafleet_network_basic.png",
              "teslafleet_bronze_to_silver.png", "teslafleet_full_architecture.png",
              "teslafleet_overview_flow.png", "teslafleet_serving_path.png",
              "teslafleet_onboarding.png", "teslafleet_security_flow.png"):
        p = os.path.join(out_dir, f)
        print(" ", p, os.path.getsize(p), "bytes")
    print(" ", pdf_path, os.path.getsize(pdf_path), "bytes")
