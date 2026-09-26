
# GIST Dissertation Class

> Readme(en): See [readme_en](readme_en.md).

- GIST thesis template.
- GitHub에서는 `git clone` 보다 `Use this template` 사용을 권장.
- 일반적으로 사용자는 `thesis.tex`, `tex/`, `thesis.bib`, `figs/` 만 수정하면 된다.

## 0. Quick Start

### Template 사용 권장

- GitHub에서 `Use this template` 로 자신의 저장소를 먼저 만든 뒤 작업하는 것을 권장한다.
- 단순 다운로드만 필요하면 `Download ZIP` 도 가능하다.
- `git clone` 으로 시작했다면 필요 시 아래처럼 원본 remote 를 제거할 수 있다.

```bash
git remote remove origin
```

### 기본 수정 위치

- `thesis.tex`: 학위/학과/제목/저자/심사위원 등 메타데이터
- `tex/`: 초록, 본문, summary, CV
- `thesis.bib`: 참고문헌
- `figs/`: 그림 파일

### Build

```bash
latexmk -pdf thesis.tex
```

정리:

```bash
latexmk -c
```

### 공개 전 체크

- 예시 메타데이터가 남아 있지 않은지 확인
- `LICENSE` 추가 여부 결정
- 대표 출력 PDF 스크린샷 또는 샘플 PDF 제공 여부 결정
- 학교/학과별 요구사항이 다르면 README 에 차이를 명시

- 논문 메인 파일은 `thesis.tex`.
- 실제 장별 원고는 `tex/` 아래 파일들에 작성한다.
- 그림은 `figs/` 에 두고, 클래스/레이아웃 정의는 `gist/` 및 `gist.cls` 에 있다.

## 1. User-Facing Structure: `thesis.tex`

현재 `thesis.tex` 은 다음 순서로 구성된다.

1. 문서 클래스 옵션 및 전역 설정
2. 표지/초록에 들어가는 메타데이터
3. 초록, 목차, 표/그림 목록
4. 본문 chapter 입력
5. summary, bibliography, index
6. CV 입력

보통 사용자는 `thesis.tex` 의 메타데이터와 `tex/` 아래 각 파일만 수정하면 된다.

### Preamble: class option and global setup

#### `\documentclass[..., ...]{gist}`

현재 기본 형태는 다음과 같다.

```tex
\documentclass[bibieee, standard]{gist}
```

- `bibieee`: bibliography style option
- `standard`: 제출용 레이아웃
- 사용 가능한 옵션 전체는 아래 `Class Option` 절을 참고

#### Float page rule

```tex
\makeatletter
\@fpsep\textheight
\makeatother
```

figure/table 전용 페이지 배치 규칙이다. 특별한 이유가 없으면 그대로 둔다.

#### `\makeindex`

```tex
\makeindex
```

index 생성을 활성화한다. 뒤의 `\printindex` 와 함께 사용한다.

#### Legacy EPS helper

```tex
\input epsf
\def\putepsf#1{\centering \parbox{12cm}{\epsfxsize = 12cm \epsfbox{#1}}}
```

예전 EPS figure 삽입을 위한 호환 설정이다. EPS 기반 figure 를 쓰지 않으면 보통 건드리지 않는다.

### Thesis metadata

#### `\code{...}`

학위 코드와 학과 코드를 지정한다.

```tex
\code{{D/}MRE}
```

- `{B/}`: 학사
- `{M/}`: 석사
- `{D/}`: 박사
- 현재 클래스는 `MRE` 코드를 전제로 사용하고 있다.
- 학위 코드는 반드시 명시해야 한다.

#### `\degreeabbr{...}`

초록 등에 찍히는 학위 약칭을 지정한다.

```tex
\degreeabbr{PhD}
```

출력 예시는 `PhD/MRE` 와 같다. 생략하면 학위 코드에 따라 기본값이 들어간다.

#### `\college{...}`

단과대학 이름을 지정한다.

```tex
\college{College of Engineering}
```

표지 및 제출 관련 frontmatter 에 반영된다.

#### Department metadata: `\@edept`, `\@kdept`, `\@kdeptn`

현재 템플릿은 학과명을 자동으로 완성하지 않으므로 아래 3개를 직접 정의해야 한다.

```tex
\makeatletter
\def\@edept{Department of Mechanical and Robotics Engineering}
\def\@kdept{기계로봇공학부}
\def\@kdeptn{기 계 로 봇 공 학 부}
\makeatother
```

- `\@edept`: 영문 학과명
- `\@kdept`: 국문 학과명
- `\@kdeptn`: 자간을 벌린 국문 학과명

이 세 항목이 없으면 frontmatter 생성 시 에러가 난다.

#### `\etitle{...}` / `\ktitle{...}`

영문/국문 논문 제목을 지정한다.

```tex
\etitle{English Title}
\ktitle{국문 제목}
```

제목 줄바꿈이 필요하면 `\\` 대신 `\titlebreak` 를 사용한다.

```tex
\etitle{First Line \titlebreak Second Line}
```

#### `\advisor{...}` / `\coadvisor{...}`

영문 지도교수/공동지도교수 이름을 지정한다.

```tex
\advisor{Advisor Name}
%\coadvisor{Co-Advisor Name}
```

- 직함(`Prof.` 등)은 보통 넣지 않는다.
- 공동지도교수가 있으면 `\coadvisor` 를 활성화한다.

#### `\kadvisor{...}` / `\kcoadvisor{...}`

국문 지도교수/공동지도교수 이름을 지정한다.

```tex
\kadvisor{지도교수}
%\kcoadvisor{공동지도교수}
```

공동지도교수를 영문으로 넣었다면 국문 항목도 함께 맞추는 편이 안전하다.

#### `\ename{...}` / `\kname{...}`

저자 이름을 지정한다.

```tex
\ename{Author Name}
\kname{{성}{이}{름}}
```

`kname` 은 `{성}{이름1}{이름2}` 형태로 넣는다.

#### `\studentid{...}`

학번을 지정한다.

```tex
\studentid{00000000}
```

#### `\coveryear{...}`

졸업 연도를 지정한다.

```tex
\coveryear{2026}
```

#### `\advisorsigndate{Month}{Day}{Year}`

지도교수 서명 날짜를 넣는다.

```tex
\advisorsigndate{June}{1}{2026}
```

#### `\refereesigndate{Month}{Day}{Year}`

심사위원 서명 날짜를 넣는다.

```tex
\refereesigndate{June}{1}{2026}
```

`korean` 옵션을 켜면 한국어 날짜 형식으로 출력된다.

### Referee fields

심사위원은 최대 7명까지 입력할 수 있다.

- `\refereeA{...}`
- `\refereeB{...}`
- `\refereeC{...}`
- `\refereeD{...}`
- `\refereeE{...}`
- `\refereeF{...}`
- `\refereeG{...}`

예시:

```tex
\refereeA{Prof. John Smith}
\refereeB{Prof. John Doe}
\refereeC{Prof. Jane Doe}
```

### Frontmatter and body structure

#### `\dedication{...}`

dedication 페이지 문구를 지정한다.

```tex
\dedication{Dedicated to my family.}
```

#### `\hypersetup{pageanchor=false}` / `\hypersetup{pageanchor=true}`

frontmatter 와 mainmatter 사이에서 PDF page anchor 충돌을 피하기 위한 설정이다. 특별한 이유가 없으면 그대로 둔다.

#### Abstract / acknowledgement environments

현재 구조는 다음과 같다.

```tex
\begin{eabstract}
\input{tex/0_abstract_en.tex}
\end{eabstract}

\begin{kabstract}
\input{tex/0_abstract_kr.tex}
\end{kabstract}

% \begin{acknowledgements}
% \input{tex/1_ack.tex}
% \end{acknowledgements}
```

- 영문 초록은 `tex/0_abstract_en.tex`
- 국문 초록은 `tex/0_abstract_kr.tex`
- 감사의 글은 필요하면 `acknowledgements` 환경을 주석 해제해서 사용

#### TOC / list commands

```tex
\makecontents
\listtables
\listfigures
```

표나 그림이 없으면 `\listtables`, `\listfigures` 는 생략할 수 있다.

#### Main body inputs

본문 chapter 는 보통 각 파일을 `\input` 해서 구성한다.

```tex
\pagenumbering{arabic}
\setcounter{page}{1}
\input{tex/2_intro.tex}
\input{tex/3_batsoc.tex}
\input{tex/4_ixfeat.tex}
```

본문 시작 시 페이지 번호를 아라비아 숫자로 다시 1부터 시작한다.

장 순서를 바꾸거나 새 장을 추가할 때는 이 블록을 수정한다.

#### `\summary{...}`

마지막 summary chapter 는 일반 `\chapter` 대신 아래처럼 넣고 있다.

```tex
\summary{tex/5_summary.tex}
```

현재 summary 원고는 `tex/5_summary.tex` 에 있다.

#### Bibliography command

```tex
\gistbibliography{thesis}
```

- `.bib` 확장자는 쓰지 않는다.
- 현재는 `thesis.bib` 를 읽는 구조다.

#### `\printindex`

```tex
\printindex
```

index 를 실제 문서에 출력한다. `\makeindex` 와 짝을 이룬다.

### Curriculum vitae

CV 는 `thesis.tex` 안에서 직접 쓰지 않고 별도 파일을 불러온다.

```tex
\input{tex/6_curriculum vitae.tex}
```

CV 관련 항목은 `tex/6_curriculum vitae.tex` 에서 수정한다.

#### `\birthday{Month}{Day}{Year}`

```tex
\birthday{January}{1}{2000}
```

#### `\birthplace{...}`

```tex
\birthplace{Sample City, Country}
```

#### `\addr{...}`

```tex
\addr{123 Example Street, Sample District, Sample City, Country}
```

---

## 2. Commands Defined in `gist.cls`

아래는 사용자가 본문에서 직접 활용할 수 있는 utility command 들이다.

### `\subfig[caption]{width}{path}{label}`

subfigure 를 간단히 넣는 매크로.

```tex
\subfig[Example caption]{0.48\textwidth}{figs/example.pdf}{fig:example}
```

동작:

- optional caption 이 비어 있으면 캡션 텍스트 없이 카운터만 증가
- label 이 비어 있으면 `\label` 생성 안 함

### `\argmin`

수학 연산자 `argmin`.

```tex
$$x^\star = \argmin_x f(x)$$
```

### `\tcell{line1}{line2}`

2 줄짜리 표 셀을 만들 때 사용.

```tex
\tcell{Voltage}{(V)}
```

### Color helpers

- `\red{...}`
- `\blue{...}`
- `\green{...}`

예시:

```tex
\red{revision note}
```

최종 제출본에서는 색 강조를 제거하는 것이 안전하다.

### `\degc`

섭씨 기호 표기용.

```tex
25\degc{}
```

### `\tf`

작은 글자 크기 preset.

```tex
{\tf small text}
```

### `\cellset`

`makecell` 표 내부 간격 조정용.

```tex
\cellset
```

보통 표 시작 직전에 사용한다.

### `\str{...}`

취소선.

```tex
\str{obsolete text}
```



---

## 3. Class Option

기본 사용 형태:

```tex
\documentclass[bibieee]{gist}
```

옵션은 쉼표로 함께 줄 수 있다.

```tex
\documentclass[bibieee,dense]{gist}
```

### Layout mode

- `standard`
  - 제출용 레이아웃 적용
  - 넓은 줄간격과 기본 여백을 사용
- `dense`
  - 내부 검토용 모드
  - 줄간격을 압축해 페이지 수를 줄임

### Language option

- `korean`
	- 한국어 양식 제목, 심사위원 표기, 날짜 형식을 사용

예시:

```tex
\documentclass[korean,bibieee,standard]{gist}
```

### Bibliography style option

아래 중 하나를 선택할 수 있다.

- `bibplainnat`
- `bibunsrtnat`
- `bibabbrvnat`
- `bibieee`

일반적으로 현재 thesis 템플릿은 `bibieee` 를 사용하면 된다.

### Citation style option

아래 중 하나를 선택할 수 있다.

- `citenumeric`
- `citesuper`
- `citeauthoryear`

보통 bibliography style 과 함께 문서 클래스 옵션에 넣는다.

```tex
\documentclass[bibieee,citenumeric,standard]{gist}
```
