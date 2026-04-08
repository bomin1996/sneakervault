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
| `fix: restrict CORS policy and allowed HTTP methods` | CORS `allow_origins=["*"]` 제거, 환경변수 기반 origin 관리로 변경. `allow_methods`/`allow_headers`를 필요한 항목만 명시 | 코드 리뷰 중 CORS가 전체 origin을 허용하고 있는 걸 발견했는데, 이러면 악의적인 외부 사이트에서 API를 자유롭게 호출할 수 있어서 CSRF 공격에 노출될 수 있겠다고 판단했다. 운영 환경에서는 신뢰할 수 있는 도메인만 허용해야 한다고 생각해서 `.env`로 origin을 관리하도록 변경했고, methods와 headers도 와일드카드 대신 실제 사용하는 항목만 명시하는 방식으로 수정했다. |
| `fix: remove hardcoded SECRET_KEY default value` | 하드코딩된 `"dev-secret-key-change-in-production"` 제거, `secrets.token_urlsafe(32)`로 자동 생성되도록 변경. `field_validator`로 위험한 기본값 사용 시 앱 시작 자체를 차단 | SECRET_KEY가 코드에 그대로 박혀 있으면 레포를 볼 수 있는 누구나 JWT를 위조할 수 있다고 생각했다. `.env` 미설정 시에도 랜덤 키가 생성되게 하되, 알려진 위험한 값은 validator로 걸러서 실수로 운영에 올라가는 걸 막고 싶었다. |
| `feat: add login attempt rate limiting with Redis` | 로그인 실패 시 Redis에 시도 횟수 기록, 5회 초과 시 15분간 차단. 성공 시 카운트 초기화 | 로그인 엔드포인트에 아무런 제한이 없으면 brute force 공격으로 비밀번호를 무한히 시도할 수 있다는 게 신경 쓰였다. 이미 Redis를 사용하고 있어서 별도 인프라 추가 없이 TTL 기반으로 시도 횟수를 관리하면 되겠다고 판단했고, pipeline으로 incr/expire를 원자적으로 처리해서 race condition도 방지했다. |
| `fix: prevent API key timing attack and use enum for status comparison` | API Key 비교를 `hmac.compare_digest`로 변경, partner status 비교를 문자열에서 `PartnerStatus` Enum으로 변경 | API Key를 `==`로 비교하면 문자열 길이에 따라 응답 시간이 달라져서 공격자가 한 글자씩 키를 유추할 수 있다는 걸 알고 있었다. `hmac.compare_digest`는 항상 일정한 시간이 걸려서 이 문제를 해결할 수 있다. 또한 status를 문자열로 비교하고 있었는데, Enum이 이미 정의되어 있으면서 안 쓰고 있어서 타이포 실수 방지 겸 Enum 비교로 바꿨다. |
| `feat: add global and per-endpoint rate limiting with slowapi` | slowapi 기반 글로벌 Rate Limiting(100req/min) 적용. 로그인(10/min), 회원가입(5/min), AI 분석(10/min) 엔드포인트에 개별 제한 추가 | API에 요청 제한이 전혀 없으면 DDoS나 자동화 스크립트로 서버가 과부하될 수 있다고 생각했다. 특히 AI 분석은 OpenAI API 호출 비용이 발생하므로 남용 방지가 필수적이었고, 인증 관련 엔드포인트는 더 엄격하게 제한해야 한다고 판단했다. Redis를 storage로 사용해서 다중 인스턴스 환경에서도 일관되게 동작한다. |
| `feat: implement refresh token and token revocation` | Refresh Token 발급/갱신, 로그아웃 시 Redis 기반 토큰 블랙리스트, 토큰 만료 구분 처리 추가 | 기존에는 Access Token 하나만 발급하고 만료/폐기 처리가 없어서, 토큰이 탈취되면 만료될 때까지 막을 방법이 없었다. Refresh Token을 도입해서 Access Token 수명을 짧게 유지하면서도 사용자 경험을 해치지 않도록 했고, 로그아웃 시 토큰을 블랙리스트에 등록해서 즉시 무효화할 수 있게 했다. TTL을 토큰 만료 시간에 맞춰서 Redis 메모리가 불필요하게 쌓이지 않도록 했다. |
| `refactor: replace random price simulation with provider pattern` | 랜덤 시뮬레이션 제거, PriceProvider 추상 클래스 기반 외부 API 연동 구조로 변경. 매직 넘버 상수화, 배치 flush, 일간 리포트에 실제 알림 생성 추가 | 시세 수집이 `random.uniform`으로 동작하고 있어서 데모용으로밖에 쓸 수 없는 상태였다. 실제 운영에서는 외부 API나 크롤러에서 가격을 가져와야 하므로 Provider 패턴으로 추상화해서 데이터 소스를 교체할 수 있게 했다. 또한 일간 리포트가 통계만 계산하고 파트너에게 알림을 보내지 않고 있어서 Notification 생성까지 연결했다. |
| `feat: add Redis caching for AI price analysis` | AI 분석 결과를 Redis에 1시간 TTL로 캐싱, OpenAI API 호출 실패 시 fallback 분석으로 전환, 타임아웃 설정 추가 | AI 분석을 요청할 때마다 매번 OpenAI API를 호출하고 있었는데, 같은 상품에 대해 짧은 시간 안에 반복 요청이 들어오면 비용 낭비에 응답 시간도 느려진다고 생각했다. 시세 데이터가 30분 간격으로 수집되니까 1시간 캐싱이면 충분하다고 판단했고, API 장애 시에도 fallback으로 기본 분석을 제공해서 서비스가 중단되지 않도록 했다. |

| `feat: add email verification on registration` | 회원가입 시 이메일 인증 토큰 발급, `/verify-email` 엔드포인트 추가, User 모델에 `email_verified` 필드 추가 | 기존에는 가입하자마자 바로 모든 기능을 쓸 수 있어서 가짜 이메일로 계정을 무한히 만들 수 있었다. 이메일 인증 단계를 추가해서 실제 이메일 소유자만 서비스를 이용하도록 하고 싶었다. 토큰 기반으로 구현해서 별도 인증 코드 저장 없이 JWT만으로 검증이 가능하도록 했다. |
| `fix: add notification deduplication` | 동일 상품/타입의 알림이 30분 내에 이미 존재하면 중복 생성 차단, 매직 넘버 상수화, 불필요한 중간 커밋 제거 | 시세 수집이 30분 간격인데 수집 시점에 여러 상품의 가격이 동시에 바뀌면 같은 알림이 반복 생성될 수 있다고 생각했다. 파트너 입장에서 같은 내용의 알림이 쌓이면 중요한 알림을 놓칠 수 있으니까, 수집 주기에 맞춰 30분 윈도우로 중복을 걸러냈다. |
| `test: add comprehensive test coverage for all endpoints` | Product, Price, Notification, Admin 테스트 추가 (46개 테스트). Redis mock, admin/partner fixture 구성, 엣지 케이스 포함 | 기존에 테스트가 auth와 partner 등록 정도만 있어서 핵심 비즈니스 로직이 검증되지 않고 있었다. 모든 엔드포인트에 대해 정상/비정상 케이스를 커버하도록 테스트를 작성했고, Redis를 mock으로 대체해서 외부 의존성 없이 테스트가 돌아가도록 했다. |
| `feat: add structured logging and global error handling` | 요청별 로깅 미들웨어(method, path, status, duration), 글로벌 예외 핸들러, 구조화된 로그 포맷 추가 | 운영 중 문제가 생겼을 때 로그가 없으면 원인 파악이 불가능하다. 모든 요청에 대해 응답 시간을 포함한 로그를 남기도록 했고, 처리되지 않은 예외가 500으로 빠지는 경우에도 스택 트레이스를 기록하도록 했다. 나중에 ELK나 CloudWatch 같은 로그 수집 시스템 연동 시 파싱하기 쉬운 포맷으로 설정했다. |
| `refactor: extract magic numbers to named constants` | prices.py의 하드코딩된 limit(50, 30)을 상수로 추출, admin.py의 status 문자열 비교를 Enum으로 변경 | 코드에 50, 30 같은 숫자가 의미 없이 박혀 있으면 나��에 왜 이 값인지 파악하기 어렵고, 여러 곳에서 같은 값을 쓸 때 ��일치가 생길 수 있다. 상수로 이름을 붙여서 의도를 명확하게 했고, admin 통계 쿼리에서도 문자열 대신 Enum을 써서 타이포 방지와 일관성을 확보했다. |

## License

MIT
