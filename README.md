# SneakerVault

리셀 상품 시세 추적 및 파트너 관리 플랫폼 API

## Overview

SneakerVault는 리셀 상품의 시세를 실시간으로 추적하고, 파트너(판매자)에게 시세 분석 API를 제공하는 백엔드 서비스입니다.

### 주요 기능

- **파트너 관리** — 파트너 등록/승인, API Key 발급, 등급(Tier) 관리
- **상품 관리** — 브랜드/카테고리별 상품 CRUD, 재고 관리
- **시세 추적** — 실시간 시세 수집, 가격 변동 이력 관리
- **AI 시세 분석** — LLM 기반 시세 트렌드 분석 및 가격 전략 추천
- **알림 시스템** — 시세 변동 알림, 파트너별 알림 설정
- **어드민** — 파트너 승인/관리, 대시보드 통계

## Tech Stack

| Category | Technology |
|----------|-----------|
| Framework | FastAPI |
| Database | MySQL 8.0 + SQLAlchemy 2.0 |
| Migration | Alembic |
| Cache | Redis |
| Task Queue | Celery + Redis (Broker) |
| Auth | JWT (python-jose) + bcrypt |
| AI | OpenAI API (GPT-4o-mini) |
| Container | Docker + Docker Compose |
| Test | pytest + TestClient |

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────┐
│  Partner App │────▶│  FastAPI      │────▶│  MySQL  │
│  (Frontend)  │     │  REST API    │     │         │
└─────────────┘     └──────┬───────┘     └─────────┘
                           │
┌─────────────┐     ┌──────┴───────┐     ┌─────────┐
│  Admin App   │────▶│  Celery      │────▶│  Redis  │
│  (Frontend)  │     │  Workers     │     │         │
└─────────────┘     └──────────────┘     └─────────┘
                           │
                    ┌──────┴───────┐
                    │  OpenAI API  │
                    │  (AI 분석)    │
                    └──────────────┘
```

## Quick Start

### Docker Compose (권장)

```bash
# 환경 변수 설정
cp .env.example .env

# 컨테이너 실행
docker compose up -d

# API 문서 확인
# http://localhost:8000/docs
```

### Local Development

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env

# DB 마이그레이션
alembic upgrade head

# 서버 실행
uvicorn app.main:app --reload

# Celery Worker 실행 (별도 터미널)
celery -A app.tasks.worker worker --loglevel=info

# Celery Beat 실행 (별도 터미널)
celery -A app.tasks.worker beat --loglevel=info
```

### 테스트 실행

```bash
pytest -v
```

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | 회원가입 |
| POST | `/api/v1/auth/login` | 로그인 |

### Partners
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/partners/register` | 파트너 등록 |
| GET | `/api/v1/partners/me` | 내 파트너 정보 |
| PATCH | `/api/v1/partners/me` | 파트너 정보 수정 |
| POST | `/api/v1/partners/me/regenerate-key` | API Key 재발급 |

### Products
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/products` | 상품 등록 |
| GET | `/api/v1/products` | 상품 목록 (검색/필터/페이지네이션) |
| GET | `/api/v1/products/{id}` | 상품 상세 |
| PATCH | `/api/v1/products/{id}` | 상품 수정 (시세 변동 자동 기록) |
| DELETE | `/api/v1/products/{id}` | 상품 비활성화 |

### Prices
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/prices/{product_id}/history` | 시세 이력 조회 |
| GET | `/api/v1/prices/{product_id}/trend` | 시세 트렌드 분석 |
| GET | `/api/v1/prices/{product_id}/ai-analysis` | AI 시세 분석 |

### Notifications
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/notifications` | 알림 목록 |
| POST | `/api/v1/notifications/{id}/read` | 알림 읽음 처리 |
| POST | `/api/v1/notifications/read-all` | 전체 읽음 처리 |
| GET | `/api/v1/notifications/settings` | 알림 설정 조회 |
| PUT | `/api/v1/notifications/settings` | 알림 설정 변경 |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/partners` | 전체 파트너 목록 |
| PATCH | `/api/v1/admin/partners/{id}` | 파트너 상태/등급 변경 |
| GET | `/api/v1/admin/products` | 전체 상품 목록 |
| GET | `/api/v1/admin/stats` | 대시보드 통계 |

## ERD

```
users 1──1 partners 1──N products 1──N price_histories
                    1──N notifications
                    1──N notification_settings
         products N──1 brands
         products N──1 categories
```

## Background Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| `collect_market_prices` | 30분 간격 | 시세 데이터 수집 및 알림 생성 |
| `generate_daily_price_report` | 매일 09:00 | 일간 시세 리포트 생성 |

## Project Structure

```
sneakervault/
├── app/
│   ├── api/v1/          # API 엔드포인트 (auth, partners, products, prices, admin)
│   ├── models/          # SQLAlchemy ORM 모델
│   ├── schemas/         # Pydantic 요청/응답 스키마
│   ├── services/        # 비즈니스 로직 (AI 분석, 알림)
│   ├── tasks/           # Celery 비동기 태스크
│   ├── utils/           # 유틸리티 (JWT, bcrypt)
│   ├── config.py        # 환경 설정
│   ├── database.py      # DB 연결 설정
│   └── main.py          # FastAPI 앱 진입점
├── tests/               # pytest 테스트
├── alembic/             # DB 마이그레이션
├── docker-compose.yml   # Docker 컨테이너 구성
├── Dockerfile
└── requirements.txt
```

## License

MIT
