"""
Gemini AI client for rewriting articles based on instructions.
Processes multiple articles and instructions to generate new content.
"""

import os
from google import genai
from google.genai import types
from google.genai.errors import APIError
from typing import List, Optional, Union


class RewritingClient:
    """Client for interacting with Google Gemini AI for article rewriting."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Gemini client with API key."""
        if not api_key:
            # Try to get from environment variable
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError(
                    "Gemini API key is required. Set GEMINI_API_KEY environment variable or pass it directly."
                )

        # Initialize the client with the modern SDK
        self.client = genai.Client(api_key=api_key)

    def load_prompt_template(self, prompt_file_path: str) -> str:
        """Load the prompt template from file."""
        try:
            with open(prompt_file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            raise Exception(f"Error loading prompt template: {str(e)}")

    def load_articles(self, article_file_paths: List[str]) -> List[Union[str, bytes]]:
        """Load article contents from file paths - text for .txt files, bytes for PDF files."""
        articles = []
        for file_path in article_file_paths:
            try:
                if file_path.lower().endswith(".pdf"):
                    # Handle PDF files - read as bytes for direct Gemini input
                    with open(file_path, "rb") as f:
                        pdf_content = f.read()
                        if pdf_content:
                            articles.append(pdf_content)
                else:
                    # Handle text files
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            articles.append(content)
            except Exception as e:
                print(f"Warning: Could not load article from {file_path}: {str(e)}")
        return articles

    def load_instruction(self, instruction_file_path: str) -> str:
        """Load instruction content from file."""
        try:
            with open(instruction_file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            return ""  # Return empty string if no instruction file

    def _build_content_parts(
        self, prompt_template: str, articles: List[Union[str, bytes]], instruction: str
    ) -> List:
        """Build content parts for Gemini API including text and file uploads."""

        # Start with the text prompt
        text_prompt = prompt_template + "\n\n"

        # Add text articles to the prompt
        text_articles = [article for article in articles if isinstance(article, str)]
        if text_articles:
            text_prompt += "TEXT ARTICLES TO PROCESS:\n"
            for i, article in enumerate(text_articles, 1):
                text_prompt += f"\n--- Text Article {i} ---\n{article}\n"

        # Add instruction/guideline
        if instruction:
            text_prompt += f"\nGUIDELINE/INSTRUCTION:\n{instruction}\n"
        else:
            text_prompt += "\nGUIDELINE/INSTRUCTION: No specific instruction provided. Use your best judgment for rewriting.\n"

        # Add final instruction
        pdf_articles = [article for article in articles if isinstance(article, bytes)]
        if pdf_articles:
            text_prompt += f"\nI'm also providing {len(pdf_articles)} PDF file(s) for you to process along with the text articles."

        text_prompt += "\nPlease process all the articles (both text and PDF) according to the guideline and generate a new, comprehensive article."

        # Build content parts list
        content_parts = [text_prompt]

        # Add PDF files as separate parts
        for pdf_content in pdf_articles:
            content_parts.append({"mime_type": "application/pdf", "data": pdf_content})

        return content_parts

    def process_task(self, user_folder: str, prompt_file_path: str) -> str:
        """
        Process a rewriting task with articles, instruction, and prompt.

        Args:
            user_folder: Path to user's folder containing articles and instruction
            prompt_file_path: Path to the prompt template file

        Returns:
            Generated rewritten content
        """
        try:
            # Load prompt template
            prompt_template = self.load_prompt_template(prompt_file_path)

            # Find all article files in user folder
            article_files = []
            if os.path.exists(user_folder):
                for filename in os.listdir(user_folder):
                    if filename.startswith("input") and (
                        filename.endswith(".txt") or filename.endswith(".pdf")
                    ):
                        article_files.append(os.path.join(user_folder, filename))

            # Load articles
            articles = self.load_articles(article_files)
            if not articles:
                raise Exception("No articles found to process")

            # Load instruction
            instruction_file = os.path.join(user_folder, "instruction.txt")
            instruction = self.load_instruction(instruction_file)

            # Build content parts (text + PDF files)
            content_parts = self._build_content_parts(
                prompt_template, articles, instruction
            )

            # Send to Gemini using modern SDK with mixed content
            response = self.client.models.generate_content(
                model="gemini-1.5-flash", contents=content_parts
            )

            if response.text:
                return response.text
            else:
                raise Exception("No response generated from Gemini AI")

        except APIError as e:
            raise Exception(f"Gemini API error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error processing task: {str(e)}")
