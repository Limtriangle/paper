# GIST Dissertation Class

- GIST thesis template.
- On GitHub, `Use this template` is recommended over `git clone`.
- In most cases, users only need to edit `thesis.tex`, `tex/`, `thesis.bib`, and `figs/`.

## 0. Quick Start

### Recommended workflow

- Prefer creating a new repository with `Use this template` before starting your own work.
- If you only need a snapshot, `Download ZIP` is also fine.
- If you started with `git clone`, you can remove the upstream remote if needed:

```bash
git remote remove origin
```

### Main files to edit

- `thesis.tex`: degree / department / title / author / committee metadata
- `tex/`: abstracts, chapters, summary, CV
- `thesis.bib`: bibliography
- `figs/`: figures

### Build

```bash
latexmk -pdf thesis.tex
```

Clean auxiliary files:

```bash
latexmk -c
```

### Pre-release checklist

- Confirm that no real personal metadata remains in the sample files
- Decide whether to add a `LICENSE`
- Decide whether to provide a sample PDF or screenshots
- Document any department-specific requirements in the README

- The main dissertation file is `thesis.tex`.
- The actual chapter drafts are written in the files under `tex/`.
- Figures are stored in `figs/`, and the class/layout definitions are in `gist/` and `gist.cls`.

## 1. User-Facing Structure: `thesis.tex`

The current `thesis.tex` is organized in the following order:

1. Document class options and global settings
2. Metadata for the cover and abstract
3. Abstract, table of contents, and lists of tables/figures
4. Main body chapter inputs
5. Summary, bibliography, and index
6. CV input

In most cases, users only need to modify the metadata in `thesis.tex` and the individual files under `tex/`.

### Preamble: class option and global setup

#### `\documentclass[..., ...]{gist}`

The current default form is as follows:

```tex
\documentclass[bibieee, standard]{gist}
```

- `bibieee`: bibliography style option
- `standard`: submission layout
- For the full list of available options, see the `Class Option` section below

#### Float page rule

```tex
\makeatletter
\@fpsep\textheight
\makeatother
```

This is the placement rule for figure/table-only pages. Leave it as is unless there is a specific reason to change it.

#### `\makeindex`

```tex
\makeindex
```

This enables index generation. It is used together with `\printindex` later.

#### Legacy EPS helper

```tex
\input epsf
\def\putepsf#1{\centering \parbox{12cm}{\epsfxsize = 12cm \epsfbox{#1}}}
```

This is a compatibility setting for legacy EPS figure insertion. If you do not use EPS-based figures, you usually do not need to touch it.

### Thesis metadata

#### `\code{...}`

Specifies the degree code and department code.

```tex
\code{{D/}MRE}
```

- `{B/}`: bachelor's
- `{M/}`: master's
- `{D/}`: doctoral
- The current class assumes the `MRE` code.
- The degree code must be explicitly specified.

#### `\degreeabbr{...}`

Specifies the abbreviated degree label printed in places such as the abstract.

```tex
\degreeabbr{PhD}
```

An example output is `PhD/MRE`. If omitted, a default value is filled in according to the degree code.

#### `\college{...}`

Specifies the college name.

```tex
\college{College of Engineering}
```

This is reflected in the cover and submission-related frontmatter.

#### Department metadata: `\@edept`, `\@kdept`, `\@kdeptn`

The current template does not automatically complete the department name, so the following three items must be defined manually.

```tex
\makeatletter
\def\@edept{Department of Mechanical and Robotics Engineering}
\def\@kdept{기계로봇공학부}
\def\@kdeptn{기 계 로 봇 공 학 부}
\makeatother
```

- `\@edept`: English department name
- `\@kdept`: Korean department name
- `\@kdeptn`: spaced Korean department name

If these three items are missing, an error occurs when generating the frontmatter.

#### `\etitle{...}` / `\ktitle{...}`

Specifies the English/Korean dissertation titles.

```tex
\etitle{English Title}
\ktitle{국문 제목}
```

If a line break is needed in the title, use `\titlebreak` instead of `\\`.

```tex
\etitle{First Line \titlebreak Second Line}
```

#### `\advisor{...}` / `\coadvisor{...}`

Specifies the English name of the advisor/co-advisor.

```tex
\advisor{Advisor Name}
%\coadvisor{Co-Advisor Name}
```

- Titles such as `Prof.` are usually omitted.
- If there is a co-advisor, enable `\coadvisor`.

#### `\kadvisor{...}` / `\kcoadvisor{...}`

Specifies the Korean name of the advisor/co-advisor.

```tex
\kadvisor{지도교수}
%\kcoadvisor{공동지도교수}
```

If you provide the co-advisor in English, it is safer to match the Korean field as well.

#### `\ename{...}` / `\kname{...}`

Specifies the author name.

```tex
\ename{Author Name}
\kname{{성}{이}{름}}
```

`kname` should be provided in the form `{family}{given1}{given2}`.

#### `\studentid{...}`

Specifies the student ID.

```tex
\studentid{00000000}
```

#### `\coveryear{...}`

Specifies the graduation year.

```tex
\coveryear{2026}
```

#### `\advisorsigndate{Month}{Day}{Year}`

Sets the advisor signature date.

```tex
\advisorsigndate{June}{1}{2026}
```

#### `\refereesigndate{Month}{Day}{Year}`

Sets the committee signature date.

```tex
\refereesigndate{June}{1}{2026}
```

If the `korean` option is enabled, it is printed in Korean date format.

### Referee fields

Up to 7 committee members can be entered.

- `\refereeA{...}`
- `\refereeB{...}`
- `\refereeC{...}`
- `\refereeD{...}`
- `\refereeE{...}`
- `\refereeF{...}`
- `\refereeG{...}`

Example:

```tex
\refereeA{Prof. John Smith}
\refereeB{Prof. John Doe}
\refereeC{Prof. Jane Doe}
```

### Frontmatter and body structure

#### `\dedication{...}`

Specifies the text on the dedication page.

```tex
\dedication{Dedicated to my family.}
```

#### `\hypersetup{pageanchor=false}` / `\hypersetup{pageanchor=true}`

This setting avoids PDF page anchor conflicts between the frontmatter and the mainmatter. Leave it unchanged unless there is a specific reason.

#### Abstract / acknowledgement environments

The current structure is as follows:

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

- The English abstract is in `tex/0_abstract_en.tex`
- The Korean abstract is in `tex/0_abstract_kr.tex`
- For acknowledgements, uncomment the `acknowledgements` environment if needed

#### TOC / list commands

```tex
\makecontents
\listtables
\listfigures
```

If there are no tables or figures, `\listtables` and `\listfigures` may be omitted.

#### Main body inputs

The main body chapters are typically composed by `\input`-ing each file.

```tex
\pagenumbering{arabic}
\setcounter{page}{1}
\input{tex/2_intro.tex}
\input{tex/3_batsoc.tex}
\input{tex/4_ixfeat.tex}
```

At the start of the main body, page numbering is reset to Arabic numerals starting from 1.

When changing chapter order or adding a new chapter, modify this block.

#### `\summary{...}`

The final summary chapter is inserted as follows instead of using a regular `\chapter`.

```tex
\summary{tex/5_summary.tex}
```

The current summary draft is in `tex/5_summary.tex`.

#### Bibliography command

```tex
\gistbibliography{thesis}
```

- Do not include the `.bib` extension.
- The current setup reads `thesis.bib`.

#### `\printindex`

```tex
\printindex
```

Prints the index in the actual document. It pairs with `\makeindex`.

### Curriculum vitae

The CV is not written directly inside `thesis.tex`; it is loaded from a separate file.

```tex
\input{tex/6_curriculum vitae.tex}
```

Edit CV-related items in `tex/6_curriculum vitae.tex`.

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

Below are utility commands that users can directly use in the main text.

### `\subfig[caption]{size}{path}{label}`

A macro for inserting subfigures more simply.

```tex
% Subfigure macro
% \subfig[Caption]{Size}{Fig_Path}{Label}
\begin{figure}[t]
    \centering
    \subfig[Cat1.]{0.45\textwidth}{figs/cat1}{fig:cat2_1}
    \hfill
    \subfig[Cat2.]{0.45\textwidth}{figs/cat1}{fig:cat2_2}
    \caption{Cats! with subfig macro}
    \label{fig:cats2}
\end{figure}
```

Behavior:

- If the optional caption is empty, only the counter is incremented without caption text
- If the label is empty, no `\label` is generated

### `\argmin`

The mathematical operator `argmin`.

```tex
$$x^\star = \argmin_x f(x)$$
```

### `\tcell{line1}{line2}`

Used to create a two-line table cell.

```tex
\tcell{Voltage}{(V)}
```

### Color helpers

- `\red{...}`
- `\blue{...}`
- `\green{...}`

Example:

```tex
\red{revision note}
```

For the final submission version, removing color emphasis is the safer choice.

### `\degc`

For writing the degree Celsius symbol.

```tex
25\degc{}
```

### `\tf`

A small-font-size preset.

```tex
{\tf small text}
```

### `\cellset`

For adjusting internal spacing in `makecell` tables.

```tex
\cellset
```

It is usually used immediately before the start of a table.

### `\str{...}`

Strikethrough.

```tex
\str{obsolete text}
```

---

## 3. Class Option

Basic usage:

```tex
\documentclass[bibieee]{gist}
```

Options can be combined with commas.

```tex
\documentclass[bibieee,dense]{gist}
```

### Layout mode

- `standard`
  - Applies the submission layout
  - Uses wider line spacing and default margins
- `dense`
  - Internal review mode
  - Compresses line spacing to reduce page count

### Language option

- `korean`
  - Uses Korean-format titles, committee labels, and date formatting

Example:

```tex
\documentclass[korean,bibieee,standard]{gist}
```

### Bibliography style option

Choose one of the following.

- `bibplainnat`
- `bibunsrtnat`
- `bibabbrvnat`
- `bibieee`

In general, the current thesis template should use `bibieee`.

### Citation style option

Choose one of the following.

- `citenumeric`
- `citesuper`
- `citeauthoryear`

It is usually provided in the document class options together with the bibliography style.

```tex
\documentclass[bibieee,citenumeric,standard]{gist}
```
