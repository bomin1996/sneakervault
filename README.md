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
│  Partner App │────▶│  FastAPI    │──▶│  MySQL  │
│  (Frontend)  │     │  REST API   │     │         │
└─────────────┘     └──────┬───────┘     └─────────┘
                           │
┌─────────────┐     ┌──────┴───────┐     ┌─────────┐
│  Admin App   │────▶│  Celery    │───▶│  Redis  │
│  (Frontend)  │     │  Workers    │     │         │
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

## Changelog

| 커밋 | 변경 사항 | 이유 |
|------|----------|------|
| `fix: restrict CORS policy and allowed HTTP methods` | CORS 와일드카드 제거, `.env` 기반 origin 관리로 변경 | 전체 origin 허용은 CSRF 공격에 노출되므로 신뢰할 수 있는 도메인만 허용하도록 변경했다. |
| `fix: remove hardcoded SECRET_KEY default value` | SECRET_KEY 자동 생성 + validator로 위험한 기본값 차단 | 코드에 박힌 키는 JWT 위조에 악용될 수 있어서 랜덤 생성과 검증을 추가했다. |
| `feat: add login attempt rate limiting with Redis` | 로그인 5회 실패 시 15분 차단, Redis TTL 기반 | brute force 방지를 위해 기존 Redis 인프라를 활용한 시도 횟수 제한을 적용했다. |
| `fix: prevent API key timing attack and use enum for status` | `hmac.compare_digest`로 상수 시간 비교, Enum 비교로 변경 | `==` 비교의 타이밍 공격 취약점을 제거하고, 문자열 비교를 Enum으로 통일했다. |
| `feat: add global and per-endpoint rate limiting` | slowapi 글로벌(100/min) + 엔드포인트별 개별 제한 | DDoS 방지와 OpenAI API 비용 남용을 막기 위해 요청 제한을 도입했다. |
| `feat: implement refresh token and token revocation` | Refresh Token + Redis 블랙리스트 기반 로그아웃 | 토큰 탈취 시 즉시 무효화할 수 있는 수단이 없어서 블랙리스트 방식을 적용했다. |
| `refactor: replace random price simulation with provider pattern` | PriceProvider 추상화, 일간 리포트 알림 생성 연결 | 랜덤 시뮬레이션을 제거하고 실제 외부 API 연동이 가능한 구조로 변경했다. |
| `feat: add Redis caching for AI price analysis` | AI 분석 결과 1시간 캐싱, 실패 시 fallback 전환 | 반복 호출 시 비용 낭비를 줄이고, API 장애에도 서비스가 유지되도록 했다. |
| `feat: add email verification on registration` | 이메일 인증 토큰 발급 + `/verify-email` 엔드포인트 | 가짜 이메일 가입을 방지하기 위해 JWT 기반 이메일 인증 단계를 추가했다. |
| `fix: add notification deduplication` | 30분 윈도우 내 동일 알림 중복 생성 차단 | 시세 수집 시 같은 알림이 반복 생성되어 중요한 알림이 묻히는 걸 방지했다. |
| `test: add comprehensive test coverage` | 전체 엔드포인트 테스트 추가 (10개 → 47개) | 핵심 비즈니스 로직이 검증되지 않고 있어서 Redis mock 기반으로 전체 커버리지를 확대했다. |
| `feat: add structured logging and global error handling` | 요청별 로깅 미들웨어 + 글로벌 예외 핸들러 | 운영 중 원인 파악을 위해 응답 시간 포함 로그와 미처리 예외 기록을 추가했다. |
| `refactor: extract magic numbers to named constants` | 하드코딩된 숫자 상수화, status Enum 통일 | 의미 없는 숫자의 의도를 명확히 하고 타이포 방지를 위해 상수와 Enum으로 변경했다. |
| `fix: hide API key from partner GET responses` | 조회 시 마지막 4자리만 노출, 발급 시에만 전체 반환 | API Key가 일반 조회 응답에 노출되어 네트워크 로그에서 유출될 수 있어서 마스킹 처리했다. |
| `feat: add admin audit log for partner management` | AuditLog 모델, 변경 전후 값 JSON 기록 | Admin 작업의 추적이 불가능해서 감사 로그를 추가하여 책임 소재를 파악할 수 있게 했다. |

## License

MIT
