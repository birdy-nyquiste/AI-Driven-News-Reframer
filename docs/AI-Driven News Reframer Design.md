# AI-Driven News Reframer Design

**Author:** Birdy
**Date:** 2025/09/24

# 1. Overview

**Problem Statement:** This project focuses on providing an automated solution for customized news article reframing and rewriting, driven by AI.

**Proposed Solution (High-Level):** This is a web application built with Python, Flask, and an interactive frontend.

**Timeline:** The project is estimated to be delivered by September 30, 2025.

# 2. Goals

## 2.1 Input

- **2.1.1 One or more news articles on the same topic**
    - Supported formats include plain text, PDF files, and web URLs.
- **2.1.2 Custom Reframing Instructions**
    - User-provided text to be used as part of the prompt for the Large Language Model (LLM).

## 2.2 Output

- **2.2.1 Reframed news article based on provided articles and instructions**
    - Supported formats include plain text and PDF files.
- **2.2.2 AI-generated images based on the reframed news article**
    - The user can choose whether to include these images in the reframed article.

## 2.3 Language Model

- **2.3.1 Google Gemini API**
    - Handles prompts, instructions, and different input types.
    - Generates reframed articles and images.

# 3. System Architecture

## 3.1 Frontend

- Introductory/Welcome page
- Task creation
    - Users can add articles one at a time by choosing from a text input box, uploading a PDF, or pasting a URL.
    - Add custom instructions.
- Task progress display
- Results display

## 3.2 Backend

- API endpoints
- Google Gemini API integration
- Text extraction from various sources

# 4. Deployment

- To Be Determined (TBD)