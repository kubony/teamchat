## 20240718 GPT4o
#### 현재 개발 상황

1. **인증 시스템 (app/api/auth.py)**
    
    - 사용자 생성, 로그인, 토큰 발급 기능 구현
    - JWT 기반의 인증 시스템 구축
    - 현재 사용자 정보 조회 엔드포인트 구현
2. **라우팅 설정 (app/api/routes.py)**
    
    - 각 기능별 라우터를 중앙에서 관리하도록 구성
    - Auth, Meal, Image, CGM(LibreView) 라우터 등록
3. **의존성 관리 (app/api/deps.py)**
    
    - 데이터베이스 세션 의존성 함수 구현
4. **식사 관련 API (app/api/meal.py)**
    
    - 기본적인 엔드포인트 구조만 구현된 상태
    - 실제 비즈니스 로직은 아직 미구현
5. **CGM 데이터 관리 (app/api/cgm.py)**
    
    - LibreView API를 통한 CGM 데이터 업데이트 기능 구현
    - 사용자별 CGM 데이터 업데이트 엔드포인트 구현
6. **이미지 업로드 및 관리 (app/api/image.py)**
    
    - S3를 이용한 이미지 업로드 기능 구현
    - 비동기 처리를 통한 효율적인 파일 업로드 구현
    - 사용자별 이미지 조회 기능 구현
    - 이미지 상태 관리를 위한 JSONB 컬럼 도입 검토 중
7. **데이터베이스 모델 (app/models/)**
    
    - User, Image, Meal 등의 기본 모델 구현
    - SQLAlchemy ORM을 사용한 데이터베이스 상호작용
8. **환경 설정 (app/core/config.py)**
    
    - 환경 변수 기반의 설정 관리 구현
    - 개발, 테스트, 운영 환경별 설정 분리
9. **데이터베이스 마이그레이션 (alembic)**
    
    - Alembic을 사용한 데이터베이스 스키마 버전 관리 구현
10. **에러 처리 및 로깅**
    
    - 전역 예외 처리기 구현
    - Loguru를 사용한 로깅 시스템 구축 중

### Description

#### 2024.07.20 08:35

#description

##### Head of Product

##### Claude 3.5 Sonnet

현재 개발 상황:

1. 백엔드:
    - JWT 기반 사용자 인증 시스템 구현
    - S3와 연동된 이미지 업로드 기능 구현
    - User, Image 모델 구현 (SQLAlchemy ORM 사용)
    - 이미지 업로드 및 사용자 이미지 조회 API 구현
    - 환경 변수 관리 및 환경 분리 (.env 파일 사용)
    - 기본적인 에러 처리 및 로깅 시스템 구현
2. 프론트엔드:
    - 넷플릭스 클론 UI를 기반으로 개발 중
    - 카메라 모듈 통합 작업 진행 중
3. 제품 기획:
    - 핵심 기능 정의: 식사 기록, CGM 데이터 연동, 혈당 그래프 시각화
    - 사용자 페르소나 및 사용자 여정 맵 초안 작성
    - MVP 범위 및 출시 전략 수립
4. 데이터 관리:
    - 사용자 생성 콘텐츠 관리 전략 수립 (태그 시스템, 커뮤니티 기반 검토 등)
    - 음식 데이터베이스 구축 계획 수립
5. 비즈니스 모델:
    - 기본 수익 모델 구상 (프리미엄 기능, CGM 기기 연계 판매 등)

https://claude.ai/chat/158533d8-3ebf-4c04-bb89-656c2c288665