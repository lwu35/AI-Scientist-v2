%% iclr2025_workshop.cls
%% Wrapper class file for ICLR 2025 workshop submissions
%% This simply loads the article class and iclr2025 style package

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{iclr2025_workshop}[2025/01/01 ICLR 2025 Workshop Class]

% Pass all options to article class
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax

% Load the article class with default options
\LoadClass[10pt,twocolumn]{article}

% Load the ICLR 2025 style package
\RequirePackage{iclr2025} 