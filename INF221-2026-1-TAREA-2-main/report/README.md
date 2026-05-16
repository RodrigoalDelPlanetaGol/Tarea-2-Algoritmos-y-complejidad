# AlgoReportTemplate

## Descripción

Este repositorio contiene una plantilla en **LaTeX** diseñada específicamente para la creación de informes y reportes de la asignatura **Algoritmos y Complejidad** del Departamento de Informática de la **Universidad Técnica Federico Santa María (UTFSM)**.  
La plantilla está estructurada para facilitar la redacción de tareas, reportes de laboratorio y proyectos relacionados con el análisis de algoritmos.

## Modificación de la plantilla

- Complete sus datos personales en `author.tex`.
- Los archivos `preamble.tex` y `report.tex` **no deben ser modificados**.
- La estructura del directorio `sections/` **no debe ser alterada**.  
  Solo agregue contenido en los archivos existentes y elimine las instrucciones o comentarios que se encuentran dentro de ellos.
- La estructura de **subsecciones** y **subsubsecciones** dentro de los archivos de `sections/` **no debe ser modificada**.  
  Únicamente agregue texto donde corresponda.
- El archivo `references.bib` contiene las referencias bibliográficas. Agregue las que utilice en su informe.
- El archivo `report.pdf` es el resultado final de la compilación del informe (`pdflatex` → `biber` → `pdflatex` ×2).
- Elimine las figuras o ejemplos existentes en la plantilla y reemplace por las figuras generadas en su propio informe.

## Estructura del repositorio

```bash
├── README.md
├── author.tex
├── preamble.tex
├── references.bib
├── report.pdf
├── report.tex
└── sections
    ├── abstract.tex
    ├── appendix1.tex
    ├── conclusions.tex
    ├── design_analysis.tex
    ├── design_analysis_brute_force.tex
    ├── design_analysis_dynamic_programming.tex
    ├── design_analysis_greedy.tex
    ├── experiment_dataset.tex
    ├── experiment_intro.tex
    ├── experiment_results.tex
    ├── implementations.tex
    └── introduction.tex