# Pre-Release Checklist & CI/CD Design

## Why

langchain-opendataloader-pdf는 opendataloader-pdf 릴리스에 맞춰 업데이트된다. 멀티플랫폼, 다양한 Python 버전의 사용자가 `pip install`로 설치 시 문제없도록 자동 검증 체계를 구축한다.

## 참고: 다른 프로젝트 패턴

- **langchain 공식**: Unit=매 PR(ubuntu), Integration=daily, `--disable-socket`, minimum dependency test
- **langchain 파트너**: Unit=매 PR(Python 3.10, 3.14), Integration=daily, fail-fast: false
- **docling-langchain**: 매 PR에 Python 5버전 매트릭스, semantic-release
- **공통**: 순수 Python은 OS 매트릭스 불필요. 네트워크 격리 필수. pip 캐싱 사용.

---

## CI/CD Workflow 구조

```
┌─────────────────────────────────────────────────────┐
│ test.yml (매 PR)                                    │
│   트리거: pull_request → main                        │
│   Unit test + minimum dep test                      │
│   ubuntu × Python 3.10, 3.12, 3.13                  │
│   --disable-socket (네트워크 격리)                    │
│   ~2분                                              │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ sync-upstream.yml (opendataloader-pdf 릴리스 시)      │
│   코드 생성 → Unit test → 옵션 동기화 검증 → PR 생성  │
│   ubuntu × Python 3.10, 3.13                         │
│   breaking change 감지                               │
│   ~3분                                              │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ test-full.yml (메이저 변경 or 수동)                    │
│   Unit + Integration 전체                            │
│   OS 3종 × Python 3.10, 3.13 = 6 조합               │
│   Java 21, 대용량 PDF, regression snapshot           │
│   ~10분                                             │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ release.yml (v* 태그, 이미 존재)                      │
│   빌드 + PyPI 배포                                   │
└─────────────────────────────────────────────────────┘
```

---

## test.yml — 매 PR

```yaml
name: Test
on:
  pull_request:
    branches: [main]
  workflow_dispatch:

concurrency:
  group: test-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

jobs:
  unit-test:
    strategy:
      fail-fast: false
      matrix:
        python-version: ['3.10', '3.12', '3.13']
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
      - run: pip install -e ".[dev]" pytest-socket
      - run: pytest tests/test_document_loaders.py -v --disable-socket --allow-unix-socket

  min-dep-test:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          cache: pip
      - name: Install minimum dependency versions
        run: |
          pip install "langchain-core==1.0.0" "opendataloader-pdf==2.1.0" pytest
          pip install -e . --no-deps
      - run: pytest tests/test_document_loaders.py -v --disable-socket --allow-unix-socket
```

### 포인트
- **concurrency**: 같은 PR에 새 push → 이전 실행 취소
- **fail-fast: false**: 한 Python 버전 실패해도 나머지 결과 확인
- **--disable-socket**: 네트워크 격리 (pytest-socket)
- **pip cache**: CI 속도 개선
- **timeout-minutes**: 무한 대기 방지
- **minimum dependency test**: langchain-core 1.0.0 + opendataloader-pdf 2.1.0 최소 조합

---

## sync-upstream.yml — 릴리스 동기화

### 보강 사항
- jobs 분리 (generate → test → create-pr)
- breaking change 감지 (옵션 제거/이름 변경)
- concurrency 제어
- timeout 설정
- 실패 시 알림 (PR 본문에 상세 분석)

```yaml
name: Sync upstream release
on:
  repository_dispatch:
    types: [upstream-release]
  workflow_dispatch:
    inputs:
      version:
        description: 'opendataloader-pdf version (e.g. 2.3.0)'
        required: true

concurrency:
  group: sync-upstream
  cancel-in-progress: false  # 릴리스 동기화는 취소하면 안 됨

jobs:
  generate:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    outputs:
      changed: ${{ steps.changes.outputs.changed }}
      breaking: ${{ steps.breaking.outputs.detected }}
    steps:
      - checkout langchain repo
      - checkout opendataloader-pdf (sparse: options.json + scripts)
      - setup node 20
      - run generate-langchain.mjs
      - update pyproject.toml dependency
      - check for changes
      - detect breaking changes (옵션 제거/이름 변경 감지)
      - commit + push branch

  test:
    needs: generate
    if: needs.generate.outputs.changed == 'true'
    strategy:
      fail-fast: false
      matrix:
        python-version: ['3.10', '3.13']
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - checkout sync branch
      - setup python (matrix) + pip cache
      - wait for PyPI + install
      - pytest tests/test_document_loaders.py -v --disable-socket

  create-pr:
    needs: [generate, test]
    if: needs.generate.outputs.changed == 'true'
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - create PR (pass→정식, fail→draft)
      - breaking change 있으면 PR에 ⚠️ 라벨 추가
      - PR 본문에: 변경 분석 + 테스트 결과 + breaking change 목록
```

### Breaking Change 감지 로직

generate-langchain.mjs에 추가:
- 이전 document_loaders.py의 파라미터 목록 파싱
- options.json과 비교 → 제거된 파라미터 감지
- 출력: `breaking-changes.json` (제거/이름변경된 옵션 목록)

---

## test-full.yml — 메이저 변경 시 수동 실행

```yaml
name: Full Test
on:
  workflow_dispatch:

jobs:
  full-test:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.10', '3.13']
    runs-on: ${{ matrix.os }}
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
      - uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'temurin'
      - run: pip install -e ".[dev]"
      - run: pytest tests/ -v  # unit + integration 전체
```

---

## 추가 구현 항목

### 1. CHANGELOG.md

sync-upstream PR에 자동 포함. 형식:

```markdown
## [Unreleased]
### Added
- `detect_strikethrough` parameter (from opendataloader-pdf v2.1.0)
### Changed
- `hybrid_timeout` default: "30000" → "0" (no timeout)
```

generate-langchain.mjs가 변경 분석 시 CHANGELOG 항목도 생성.

### 2. Deprecation 정책

opendataloader-pdf에서 옵션이 제거될 때:
1. langchain 로더에서 즉시 삭제하지 않음
2. DeprecationWarning 추가 → 1 마이너 버전 유지
3. 다음 메이저 버전에서 삭제

generate-langchain.mjs가 `breaking-changes.json`에서 감지 → PR에 deprecation 코드 제안 포함.

### 3. 버전 매핑 정책

| opendataloader-pdf | langchain-opendataloader-pdf | 규칙 |
|-------------------|----------------------------|------|
| v2.0.0 | v2.0.0 | 메이저 동기화 |
| v2.1.0 | v2.1.0 | 마이너 동기화 |
| v2.2.0 | v2.2.0 | 마이너 동기화 |
| v3.0.0 (breaking) | v3.0.0 | 메이저 동기화 |

메이저 버전은 opendataloader-pdf와 동기화. 마이너는 기능 추가 시 동기화.

### 4. 실패 알림

sync-upstream 실패 시:
- Draft PR 생성 (이미 구현)
- PR 본문에 실패 상세 포함 (이미 구현)
- GitHub notification으로 충분 (별도 Slack 불필요 — PR assignee가 알림 받음)

### 5. PAT 관리

- Fine-grained PAT 사용 (repo scope 최소화)
- 만료일: 1년 설정
- README CONTRIBUTING 섹션에 갱신 절차 문서화

### 6. 테스트 보강

#### pytest-socket (네트워크 격리)
- dev dependency에 `pytest-socket` 추가
- unit test에 `--disable-socket --allow-unix-socket` 플래그

#### Regression snapshot test
- samples/pdf/lorem.pdf의 text 출력을 snapshot으로 저장
- 버전 업 시 출력이 바뀌면 snapshot 업데이트 필요 → 의도적 변경인지 확인

#### 대용량 PDF 테스트 (test-full에서만)
- 100+ 페이지 PDF 처리 성능/메모리 확인
- samples/pdf/에 대용량 샘플 추가 (또는 동적 생성)

#### 에러 메시지 검증
- Java 미설치 시 에러 메시지에 설치 가이드 포함되는지
- 잘못된 format 지정 시 유효 옵션 목록 표시되는지

#### 동시성 테스트
- 여러 로더 인스턴스의 temp 디렉토리 충돌 없는지 확인
- `pytest-xdist`로 병렬 실행 시 안전한지

---

## 구현 대상 요약

### 신규 파일
| 파일 | 설명 |
|------|------|
| `.github/workflows/test.yml` | 매 PR unit test + min dep test |
| `.github/workflows/test-full.yml` | 수동 전체 테스트 (멀티플랫폼) |
| `CHANGELOG.md` | 버전별 변경 내역 |
| `tests/test_regression.py` | snapshot regression test |

### 수정 파일
| 파일 | 변경 |
|------|------|
| `.github/workflows/sync-upstream.yml` | jobs 분리 + 매트릭스 + breaking change 감지 |
| `pyproject.toml` | dev dependency에 pytest-socket 추가 |
| `scripts/generate-langchain.mjs` | breaking change 감지 + CHANGELOG 생성 추가 |
