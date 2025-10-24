# ==================== GEMINI SERVICE ====================
# app/services/gemini_service.py

import os
import logging
from typing import List, Tuple, Optional, Dict, Any
import google.generativeai as genai
from app.models.registration import FormField, FormSubmission
from app.schemas.registration import FieldAnalytics

logger = logging.getLogger(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")

genai.configure(api_key=GEMINI_API_KEY)

# Use Gemini 2.5 Flash (Free tier)
MODEL_NAME = "gemini-2.5-flash"

class GeminiAnalyticsService:
    """Service to generate analytics and insights using Google Gemini API"""
    
    @staticmethod
    def format_field_data(fields: List[FormField], field_analytics: List[FieldAnalytics]) -> str:
        """Format field and analytics data into readable text for Gemini"""
        formatted_data = "FORM FIELD DATA:\n\n"
        
        for analytics in field_analytics:
            field = next((f for f in fields if f.id == analytics.field_id), None)
            if not field:
                continue
            
            formatted_data += f"Question: {analytics.field_label}\n"
            formatted_data += f"Type: {analytics.field_type}\n"
            formatted_data += f"Total Responses: {analytics.total_responses}\n"
            formatted_data += f"Response Data: {analytics.response_breakdown}\n\n"
        
        return formatted_data
    
    @staticmethod
    def format_submission_sample(submissions: List[FormSubmission], sample_size: int = 5) -> str:
        """Format sample responses for qualitative analysis"""
        formatted_samples = "SAMPLE RESPONSES:\n\n"
        
        # Get text and textarea responses for qualitative analysis
        samples_collected = 0
        for submission in submissions[:sample_size]:
            if samples_collected >= sample_size:
                break
            
            formatted_samples += f"Response #{samples_collected + 1}:\n"
            for field_id, value in submission.data.items():
                if isinstance(value, str) and len(value) > 20:  # Capture longer text responses
                    formatted_samples += f"  - {value[:200]}...\n"
            formatted_samples += "\n"
            samples_collected += 1
        
        return formatted_samples
    
    @staticmethod
    def generate_form_analytics(
        form_title: str,
        fields: List[FormField],
        submissions: List[FormSubmission],
        field_analytics: List[FieldAnalytics]
    ) -> Tuple[Optional[str], Optional[List[str]]]:
        """
        Generate AI-powered analytics and insights using Gemini
        
        Args:
            form_title: Title of the form
            fields: List of form fields
            submissions: List of form submissions
            field_analytics: Pre-calculated field analytics
        
        Returns:
            Tuple of (summary: str, insights: List[str])
        """
        try:
            logger.info(f"Generating analytics for form: {form_title}")
            
            if not submissions or len(submissions) == 0:
                logger.warning("No submissions to analyze")
                return None, None
            
            # Format data for Gemini
            form_data = GeminiAnalyticsService.format_field_data(fields, field_analytics)
            sample_data = GeminiAnalyticsService.format_submission_sample(submissions)
            
            # Create comprehensive prompt
            prompt = f"""
Analyze the following form submission data and provide insights:

FORM TITLE: {form_title}
TOTAL SUBMISSIONS: {len(submissions)}

{form_data}

{sample_data}

Based on this data, please provide:
1. A 2-3 sentence SUMMARY of the key findings
2. 3-5 specific INSIGHTS as bullet points about patterns, trends, or notable observations

Format your response exactly as follows:
SUMMARY:
[Your summary here]

INSIGHTS:
- [Insight 1]
- [Insight 2]
- [Insight 3]
- [Insight 4]
- [Insight 5]

Focus on:
- Participation rates and trends
- Common responses and patterns
- Demographic insights (if available by year/school)
- Sentiment and tone of open-ended responses
- Any anomalies or interesting findings
"""
            
            logger.debug(f"Sending request to Gemini API with model: {MODEL_NAME}")
            
            # Call Gemini API
            client = genai.Client()
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                }
            )
            
            # Parse response
            response_text = response.text.strip()
            logger.debug(f"Gemini response received: {len(response_text)} characters")
            
            # Extract summary and insights
            summary = None
            insights = []
            
            if "SUMMARY:" in response_text:
                summary_section = response_text.split("SUMMARY:")[1].split("INSIGHTS:")[0].strip()
                summary = summary_section
            
            if "INSIGHTS:" in response_text:
                insights_section = response_text.split("INSIGHTS:")[1].strip()
                # Parse bullet points
                for line in insights_section.split("\n"):
                    line = line.strip()
                    if line and line.startswith("-"):
                        insight = line[1:].strip()
                        if insight:
                            insights.append(insight)
            
            logger.info(f"Successfully generated analytics: {len(insights)} insights extracted")
            return summary, insights if insights else None
            
        except Exception as e:
            logger.error(f"Error generating analytics with Gemini: {str(e)}")
            return None, None
    
    @staticmethod
    def generate_submission_summary(
        submission_data: Dict[int, Any],
        form_fields: List[FormField]
    ) -> Optional[str]:
        """
        Generate a brief AI summary of a single submission
        Useful for open-ended responses
        
        Args:
            submission_data: Student's form responses
            form_fields: Form field definitions
        
        Returns:
            AI-generated summary of the submission
        """
        try:
            # Collect text responses
            text_responses = []
            for field in form_fields:
                field_id = str(field.id)
                if field_id in submission_data:
                    value = submission_data[field_id]
                    if isinstance(value, str) and len(value) > 50:
                        text_responses.append(f"{field.label}: {value}")
            
            if not text_responses:
                return None
            
            prompt = f"""
Summarize the following form response in 1-2 sentences:

{chr(10).join(text_responses)}

Provide a concise, objective summary without adding interpretation.
"""
            
            client = genai.Client()
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                generation_config={
                    "temperature": 0.5,
                    "max_output_tokens": 200,
                }
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating submission summary: {str(e)}")
            return None
    
    @staticmethod
    def generate_trend_analysis(
        field_responses: Dict[str, int],
        field_label: str
    ) -> Optional[str]:
        """
        Generate AI insight for a specific field's response patterns
        
        Args:
            field_responses: Dict of {response: count}
            field_label: Field label for context
        
        Returns:
            AI-generated trend analysis
        """
        try:
            # Calculate percentages
            total = sum(field_responses.values())
            percentages = {k: (v/total)*100 for k, v in field_responses.items()}
            
            breakdown = "\n".join([
                f"- {response}: {count} responses ({percentages[response]:.1f}%)"
                for response, count in sorted(field_responses.items(), key=lambda x: x[1], reverse=True)
            ])
            
            prompt = f"""
Analyze the following response pattern for the question: "{field_label}"

Response Breakdown:
{breakdown}

Provide a brief 1-2 sentence insight about this trend. Focus on what's notable or interesting.
"""
            
            client = genai.Client()
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                generation_config={
                    "temperature": 0.6,
                    "max_output_tokens": 150,
                }
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating trend analysis: {str(e)}")
            return None


def generate_form_analytics(
    form_title: str,
    fields: List[FormField],
    submissions: List[FormSubmission],
    field_analytics: List[FieldAnalytics]
) -> Tuple[Optional[str], Optional[List[str]]]:
    """
    Main function to generate form analytics using Gemini
    
    This is the function called from the admin API
    """
    service = GeminiAnalyticsService()
    return service.generate_form_analytics(form_title, fields, submissions, field_analytics)