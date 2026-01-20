# Carte Blanche

**파일 감시 기반 자동화 엔진** - LAM(Large Action Model) 서비스 Phase 1 MVP

## 🚀 기능

- **파일 감시 (Watcher)**: 지정된 폴더에서 새 파일 생성 감지
- **자동 처리 (Workers)**: 파일 유형에 따른 자동화 작업 실행
- **규칙 설정 (Rules)**: JSON 기반 트리거-액션 매핑
- **웹 UI**: 직관적인 대시보드로 워크플로우 관리

## 📋 요구사항

- Python 3.10+
- pip

## 🛠️ 설치

```powershell
cd "c:\Users\LEE SEUNG GYU\Desktop\Project\Carte Blanche"
pip install -r requirements.txt
```

## ▶️ 실행

### 웹 서버 실행 (권장)
```powershell
python src/app.py
```
브라우저에서 http://localhost:5000 접속

### Watcher만 실행
```powershell
python src/watcher.py
```

## 📁 프로젝트 구조

```
Carte Blanche/
├── src/
│   ├── app.py       # Flask 웹 서버
│   ├── watcher.py   # 파일 감시자
│   ├── workers.py   # 파일 처리 함수
│   └── engine.py    # 규칙 엔진
├── web/
│   ├── index.html   # 대시보드
│   ├── style.css    # 스타일
│   └── app.js       # 프론트엔드
├── config/
│   └── rules.json   # 규칙 설정
└── requirements.txt
```

## 📐 지원 액션

| 액션 | 설명 |
|------|------|
| `process_txt` | 텍스트 파일 읽기 및 요약 생성 |
| `process_xlsx` | 엑셀 파일 데이터 추출 |

## 📜 License

MIT
