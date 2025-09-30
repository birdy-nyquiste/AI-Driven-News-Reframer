"""
Gemini AI client for rewriting articles based on instructions.
Processes multiple articles and instructions to generate new content.
"""

import os
import pathlib
from google import genai
from google.genai import types
from google.genai.errors import APIError
from typing import List, Optional, Union


class RewritingClient:
    """Client for interacting with Google Gemini AI for article rewriting."""

    def __init__(self):
        self.client = genai.Client()

    def load_prompt_template(self, prompt_file_path: str) -> str:
        """Load the prompt template from file."""
        try:
            with open(prompt_file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            raise Exception(f"Error loading prompt template: {str(e)}")

    def load_articles(self, article_file_paths: List[str]) -> List[Union[str, str]]:
        """Load article contents from file paths - text for .txt files, file paths for PDF files."""
        articles = []
        for file_path in article_file_paths:
            try:
                if file_path.lower().endswith(".pdf"):
                    # Handle PDF files - validate and store path for upload
                    if os.path.exists(file_path):
                        # Validate PDF content (basic check)
                        with open(file_path, "rb") as f:
                            pdf_header = f.read(4)
                            if pdf_header == b"%PDF":
                                articles.append(file_path)  # Store path for upload
                            else:
                                print(
                                    f"Warning: {file_path} does not appear to be a valid PDF file"
                                )
                    else:
                        print(f"Warning: PDF file not found: {file_path}")
                else:
                    # Handle text files
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            articles.append(content)
                        else:
                            print(f"Warning: {file_path} is empty")
            except FileNotFoundError:
                print(f"Warning: File not found: {file_path}")
            except PermissionError:
                print(f"Warning: Permission denied accessing: {file_path}")
            except Exception as e:
                print(f"Warning: Could not load article from {file_path}: {str(e)}")
        return articles

    def load_instruction(
        self, instruction_file_path: str, preset_id: str = None
    ) -> str:
        """Load instruction content from file or preset."""
        # If preset_id is provided, load preset content instead
        if preset_id:
            try:
                preset_file_path = os.path.join(
                    os.path.dirname(__file__), "prompts", f"preset_{preset_id}.txt"
                )
                if os.path.exists(preset_file_path):
                    with open(preset_file_path, "r", encoding="utf-8") as f:
                        return f.read().strip()
                else:
                    print(f"Warning: Preset file not found: {preset_file_path}")
            except Exception as e:
                print(f"Warning: Error loading preset {preset_id}: {str(e)}")

        # Fall back to regular instruction file
        try:
            with open(instruction_file_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            return ""  # Return empty string if no instruction file

    def _build_content_parts(
        self, prompt_template: str, articles: List[str], instruction: str
    ) -> List:
        """Build content parts for Gemini API including text and file uploads."""

        # Start with the prompt template
        content_parts = [prompt_template]

        # Add instruction if it exists
        if instruction:
            content_parts.append(instruction)

        # Add text articles
        for article in articles:
            if isinstance(article, str) and not article.lower().endswith(".pdf"):
                content_parts.append(article)

        # Upload PDF files and add them to content parts
        for article in articles:
            if (
                isinstance(article, str)
                and article.lower().endswith(".pdf")
                and os.path.exists(article)
            ):
                try:
                    uploaded_file = self.client.files.upload(file=pathlib.Path(article))
                    content_parts.append(uploaded_file)
                except Exception as e:
                    print(f"Warning: Could not upload PDF file {article}: {str(e)}")

        return content_parts

    def process_task(
        self, user_folder: str, prompt_file_path: str, preset_id: str = None
    ) -> str:
        """
        Process a rewriting task with articles, instruction, and prompt.

        Args:
            user_folder: Path to user's folder containing articles and instruction
            prompt_file_path: Path to the prompt template file
            preset_id: Optional preset ID to use instead of instruction file

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

            # Load instruction (preset or custom)
            instruction_file = os.path.join(user_folder, "instruction.txt")
            instruction = self.load_instruction(instruction_file, preset_id)

            # Build content parts (text + PDF files)
            content_parts = self._build_content_parts(
                prompt_template, articles, instruction
            )

            # Send to Gemini using modern SDK with mixed content
            response = self.client.models.generate_content(
                model="gemini-2.5-flash", contents=content_parts
            )

            if response.text:
                return response.text
            else:
                raise Exception("No response generated from Gemini AI")

        except APIError as e:
            error_msg = f"Gemini API error: {str(e)}"
            if "pdf" in str(e).lower() or "mime" in str(e).lower():
                error_msg += "\nThis might be related to PDF processing. Please ensure the PDF file is valid and not corrupted."
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error processing task: {str(e)}"
            if "pdf" in str(e).lower():
                error_msg += "\nPDF processing error. Please check if the PDF file is valid and accessible."
            raise Exception(error_msg)
