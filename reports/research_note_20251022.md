# 🧠 연구노트 — 2025-10-22 (KST)

- 생성시각(UTC): 2025-10-22 13:30:38 UTC
- 모델: `gpt-4o-mini`
- 리포지토리: msa-ez/legacy-modernizer-frontend, uengine-oss/legacy-modernizer-backend, ahnchiyoon87/Antlr-Server
- 브랜치: main
- 작성자: {'login': 'ahnchiyoon87', 'email': 'ahnpybara@uengine.org'}

## 📦 uengine-oss/legacy-modernizer-backend

### 🔖 57a4c6e — rule 파일화
- Date: 2025-10-22 18:11:46 KST
- Risk: **medium**
- Repository: uengine-oss/legacy-modernizer-backend
- Commit Link: https://github.com/uengine-oss/legacy-modernizer-backend/commit/57a4c6e9ae3798458193042da60ac548fc7528f4

> This commit introduces significant enhancements to the project, including the addition of new package versions and refactoring of the controller generation code. A new PromptLoader class has been implemented to improve prompt handling across multiple files. The service skeleton generation process has also been modified with added YAML rules for Spring Boot application migration. Furthermore, various transformation rules related to Spring Boot and PL/SQL have been introduced to support code automation, while also providing SQLAlchemy model generation rules for Python. The changes enhance language processing logic, add integration test cases, and improve overall code readability, aiming to refine the structure and introduce new functionalities to the existing system.

**📁 변경된 파일들:**
- `Pipfile` (modified, risk=medium)
  - pyyaml과 jinja2 패키지 버전 추가.
- `convert/create_controller.py` (modified, risk=medium)
  - 컨트롤러 생성을 위한 코드 리팩토링 및 메서드 통합.
- `convert/create_controller_skeleton.py` (removed, risk=high)
  - 컨트롤러 스켈레톤 생성 관련 코드 삭제됨.
- `convert/create_entity.py` (modified, risk=medium)
  - PromptLoader 클래스를 추가하고, convert_entity_code 대신 사용하여 프롬프트 처리 방식 변경.
- `convert/create_repository.py` (modified, risk=medium)
  - PromptLoader 추가 및 기존 코드에서 convert_repository_code 대체.
- `convert/create_service_preprocessing.py` (modified, risk=medium)
  - PromptLoader를 추가하여 LLM 호출 방식 개선, JSON 구조에 변환됨.
- `convert/create_service_skeleton.py` (modified, risk=medium)
  - 서비스 스켈레톤 생성 방식 변경 및 프롬프트 로더 사용 추가.
- `requirements.txt` (modified, risk=medium)
  - pyyaml과 jinja2 패키지 추가.
- `rules/java/command.yaml` (added, risk=medium)
  - Command 클래스 생성 규칙 추가로 스프링 부트 애플리케이션으로의 마이그레이션 지원.
- `rules/java/controller.yaml` (added, risk=medium)
  - Spring Boot REST Controller 메서드 생성 규칙 추가.
- `rules/java/entity.yaml` (added, risk=medium)
  - 스프링부트 JPA Entity 생성 규칙 및 템플릿 추가.
- `rules/java/repository.yaml` (added, risk=medium)
  - Spring Data JPA Repository 메서드 생성 지침을 추가했습니다.
- `rules/java/service.yaml` (added, risk=medium)
  - Spring Boot 서비스 메서드 바디 생성을 위한 규칙 추가.
- `rules/java/service_exception.yaml` (added, risk=medium)
  - PL/SQL EXCEPTION 블록을 Java try-catch로 변환하는 규칙 추가.
- `rules/java/service_skeleton.yaml` (added, risk=medium)
  - Spring Boot 메서드 시그니처 생성 규칙 추가.
- `rules/java/service_summarized.yaml` (added, risk=medium)
  - Spring Boot 서비스 스켈레톤 생성 규칙 추가. SP 코드를 Java로 변환하는 방법 명시.
- `rules/java/variable.yaml` (added, risk=medium)
  - PL/SQL 변수를 Java 타입으로 변환하는 규칙 추가.
- `rules/python/entity.yaml` (added, risk=medium)
  - Python용 SQLAlchemy ORM 모델 생성을 위한 역할과 규칙 정의 추가.
- `service/router.py` (modified, risk=medium)
  - 요청 JSON에서 targetLang을 추가로 추출하고 처리 로직 수정.
- `service/service.py` (modified, risk=medium)
  - ServiceOrchestrator 초기화 시 target_lang 인자 추가 및 서비스와 컨트롤러 생성 로직 수정.
- `test/test_converting.py` (modified, risk=medium)
  - 타겟 언어 파라미터 추가 및 통합 테스트 케이스 구현.
- `test/test_understanding.py` (modified, risk=low)
  - 주석 삭제로 코드 가독성 개선.
- `util/prompt_loader.py` (added, risk=medium)
  - 프롬프트 로더 모듈 추가, 역할 파일 로드 및 검증 기능 포함.

### 🔖 e0c012d — 예외처리 및 out 파라미터 처리
- Date: 2025-10-22 13:37:33 KST
- Risk: **medium**
- Repository: uengine-oss/legacy-modernizer-backend
- Commit Link: https://github.com/uengine-oss/legacy-modernizer-backend/commit/e0c012d32be825a5009cbabed0aa66763b62f651

> 본 커밋은 예외 처리 및 OUT 파라미터 처리 방식을 개선하여 성능 및 안정성을 높이는 작업을 수행하였습니다. TRY/EXCEPTION 구조의 개선과 PL/SQL에서 Java로의 변환 기능 추가가 포함되어 있습니다. 전체적으로 엔티티 클래스와 메소드의 이름 변경과 데이터 유효성 검증이 이루어져 안전성을 증가시키는 방향으로 진행되었습니다.

**📁 변경된 파일들:**
- `convert/create_service_preprocessing.py` (modified, risk=medium)
  - EXCEPTION 노드 처리 로직 추가 및 TRY/EXCEPTION 구조 개선.
- `convert/create_service_skeleton.py` (modified, risk=medium)
  - OUT 파라미터 처리 방식 개선 및 성능 최적화 적용
- `prompt/convert_service_prompt.py` (modified, risk=medium)
  - PL/SQL EXCEPTION 블록을 Java try-catch 구조로 변환하는 기능 추가.
- `prompt/convert_service_skeleton_prompt.py` (modified, risk=medium)
  - 입출력 파라미터 및 반환타입 결정 로직 규칙 개선.
- `test/test_converting_results.json` (modified, risk=medium)
  - 엔티티 클래스 및 쿼리 메소드 이름 변경, 주석 추가 및 데이터 유효성 검증 개선.
- `util/llm_client.py` (modified, risk=medium)
  - API 키 초기화 및 모델 버전 변경, 안전성 증가.

### 🔖 41e7c88 — fixed 인자 이슈
- Date: 2025-10-22 10:31:11 KST
- Risk: **low**
- Repository: uengine-oss/legacy-modernizer-backend
- Commit Link: https://github.com/uengine-oss/legacy-modernizer-backend/commit/41e7c8870396a5d3f945835984175f93ca7f1823

> 이 커밋은 'create_service_preprocessing.py' 파일에서 project_name의 기본값을 'demo'로 설정하고, 'service.py'에서 convert_to_springboot 함수에 project_name 추가 매개변수를 추가했습니다. 이는 코드의 유연성을 높이고 사용자가 명시적으로 project_name을 지정할 수 있게 하여 기능 향상을 도모합니다.

**📁 변경된 파일들:**
- `convert/create_service_preprocessing.py` (modified, risk=low)
  - project_name 기본값을 'demo'로 설정했습니다.
- `service/service.py` (modified, risk=low)
  - convert_to_springboot 함수에 project_name 추가 매개변수 추가.

### 🔖 9c9b3c7 — 리팩토링 convert
- Date: 2025-10-22 09:44:28 KST
- Risk: **medium**
- Repository: uengine-oss/legacy-modernizer-backend
- Commit Link: https://github.com/uengine-oss/legacy-modernizer-backend/commit/9c9b3c7a48ce27f8af56c70807f83617e9c5d2bb

> 이번 커밋은 코드 리팩토링과 최적화를 통해 전반적인 구조 개선과 성능 향상을 목표로 하고 있습니다. __slots__의 추가로 메모리 사용이 최적화되었고, 로깅 메시지가 향상되었습니다. langchain 모듈의 경로 변경 및 관련 import 업데이트를 통해 모듈 간의 연관성을 높였습니다. 그러나 서비스 후처리 코드의 전체 삭제와 여러 테스트 파일의 제거가 있어 신중한 점검이 필요합니다. 새로운 테스트가 추가되었지만, 기존 기능 일부가 중단될 위험이 있으며, 이는 미래의 유지보수에 더해질 수 있는 잠재적인 문제를 나타냅니다.

**📁 변경된 파일들:**
- `Pipfile` (modified, risk=medium)
  - 새로운 패키지 추가 및 일부 패키지 삭제.
- `convert/create_config_files.py` (modified, risk=low)
  - ConfigFilesGenerator 클래스에 __slots__ 추가로 메모리 최적화.
- `convert/create_controller.py` (modified, risk=medium)
  - 컨트롤러 생성 로직을 개선하고 매니저 클래스를 추가하여 코드 구조를 정리함.
- `convert/create_controller_skeleton.py` (modified, risk=medium)
  - 컨트롤러 스켈레톤 생성 로직을 클래스 형태로 리팩토링함.
- `convert/create_entity.py` (modified, risk=medium)
  - 로깅 메시지를 개선하고, __slots__를 추가하여 메모리 사용 최적화.
- `convert/create_main.py` (modified, risk=low)
  - __slots__ 추가로 메모리 사용 최적화.
- `convert/create_repository.py` (modified, risk=medium)
  - 슬롯 사용 정의 추가 및 로깅 메시지 개선.
- `convert/create_service_postprocessing.py` (removed, risk=high)
  - 서비스 후처리 코드 전체가 삭제되었습니다.
- `convert/create_service_preprocessing.py` (modified, risk=medium)
  - 서비스 전처리 기능 개선과 코드 최적화, 비동기 파일 저장 추가.
- `convert/create_service_skeleton.py` (modified, risk=medium)
  - 클래스에 __slots__ 추가 및 로깅 메시지 개선.
- `prompt/convert_command_prompt.py` (modified, risk=medium)
  - langchain 패키지의 import 경로 수정.
- `prompt/convert_controller_prompt.py` (modified, risk=medium)
  - 모듈 import 경로를 langchain에서 langchain_core로 변경했습니다.
- `prompt/convert_entity_prompt.py` (modified, risk=medium)
  - langchain 모듈의 경로가 langchain_core로 변경되었습니다.
- `prompt/convert_repository_prompt.py` (modified, risk=medium)
  - langchain 관련 모듈의 import 경로 업데이트.
- `prompt/convert_service_prompt.py` (modified, risk=medium)
  - langchain에서 langchain_core로의 import 변경 및 프롬프트 내용 수정.
- `prompt/convert_service_skeleton_prompt.py` (modified, risk=medium)
  - langchain 모듈의 경로를 langchain_core로 변경.
- `prompt/convert_summarized_service_prompt.py` (modified, risk=medium)
  - 임포트 경로 변경 및 주석과 변환 규칙 추가. 구조적 개선.
- `prompt/convert_variable_prompt.py` (modified, risk=medium)
  - langchain 관련 모듈의 import 경로를 langchain_core로 변경.
- `prompt/understand_column_prompt.py` (modified, risk=medium)
  - langchain 의존성 경로 수정으로 코드 구조 조정.
- `prompt/understand_ddl.py` (modified, risk=medium)
  - langchain 관련 모듈 import 경로 업데이트.
- `prompt/understand_prompt.py` (modified, risk=medium)
  - langchain 모듈 경로 변경 및 import 수정.
- `prompt/understand_summarized_prompt.py` (modified, risk=medium)
  - langchain 모듈의 import 경로가 langchain_core로 변경됨.
- `prompt/understand_variables_prompt.py` (modified, risk=medium)
  - langchain 패키지 경로가 langchain_core로 변경됨.
- `service/service.py` (modified, risk=medium)
  - 서비스 및 컨트롤러 생성 로직 간소화 및 후처리 함수로 리팩토링.
- `test/find_in_txt.py` (removed, risk=high)
  - 텍스트 파일 검색과 관련된 전체 코드가 제거됨.
- `test/sum_sql_txt_kb.py` (removed, risk=medium)
  - 사용자 정의 폴더 내 .sql 및 .txt 파일 크기를 합산하는 코드 삭제
- `test/test_converting.py` (added, risk=medium)
  - Converting 과정에 대한 상세 테스트 추가. 데이터 저장 및 검증 포함.
- `test/test_converting/__init__.py` (removed, risk=low)
  - 패키지 표시 주석 제거
- `test/test_converting/_common.py` (removed, risk=medium)
  - 환경설정 및 로깅, 결과 저장 관련 기능 제거됨.
- `test/test_converting/test_1_entity.py` (removed, risk=medium)
  - 엔티티 처리 관련 테스트 파일이 삭제됨.
- `test/test_converting/test_2_repository.py` (removed, risk=medium)
  - 테스트 파일이 제거되었습니다. 관련된 정의와 실행 코드 모두 삭제.
- `test/test_converting/test_3_service_skeleton.py` (removed, risk=medium)
  - 서비스 스켈레톤 생성 관련 테스트 코드 삭제
- `test/test_converting/test_4_service.py` (removed, risk=medium)
  - 서비스 전처리 및 검증 관련 비동기 함수 전체를 제거함.
- `test/test_converting/test_5_controller.py` (removed, risk=medium)
  - test_5_controller.py 파일 삭제로, 관련 테스트 기능 제공 중단.
- `test/test_converting/test_results.json` (removed, risk=medium)
  - test_results.json 파일이 삭제되었습니다.
- `test/test_converting_results.json` (added, risk=medium)
  - 병원 프로젝트 관련 엔티티와 리포지토리 정보가 추가되었습니다.
- `test/test_understanding.py` (modified, risk=medium)
  - 이해 파이프라인에 대한 실제 테스트 구현 및 로깅 제거. Neo4j 연결을 사용하는 새 테스트 추가.
- `understand/analysis.py` (modified, risk=medium)
  - 토큰 관리 및 Node 분석 로직 최적화, 불필요한 import 제거.
- `understand/neo4j_connection.py` (modified, risk=medium)
  - 에러 핸들링 및 쿼리 최적화를 포함하여 Neo4j 연결 관리 개선.
- `util/llm_client.py` (modified, risk=medium)
  - 모델 이름 변경, 기본값과 함수 호출 최적화.
- `util/utility_tool.py` (modified, risk=medium)
  - 비동기 파일 저장 및 경로 생성 함수 최적화. 예외 처리 개선.
