"""
Tools for generating data visualizations from structured data for newsletter workflows.

This module provides CrewAI-compatible tools to:
    - Render Vega-Lite chart specifications from Jinja2 templates using structured data
    - Export charts as PNG images for inclusion in newsletters
    - Support runtime configuration of template, output directory, and file naming

Designed for seamless integration with agent-based pipelines and reproducible, automated reporting.
"""

import os
import json
from typing import Type, Optional
from pydantic import BaseModel, Field, field_validator
from crewai.tools import BaseTool
from jinja2 import Environment, FileSystemLoader
import vl_convert as vlc


class GenerateStructuredDataChartArgs(BaseModel):
    """Arguments for generating a structured data chart from time series data."""

    data: list[dict] = Field(
        ..., description="Time series data as a JSON object (list of dicts)"
    )
    chart_title: str = Field(
        default="Time Series Chart", description="Title for the chart"
    )
    chart_file_name: Optional[str] = Field(
        default=None,
        description="Base file name (without extension) for the output chart files. If None, uses chart_title with spaces replaced by underscores.",
    )
    template_name: str = Field(
        default="ipca_accumulated_regression.json.j2",
        description="Name of the Jinja2 template file to use.",
    )
    template_dir: Optional[str] = Field(
        default=None,
        description="Directory where the Jinja2 template is located. If None, defaults to templates/charts.",
    )

    output_dir: Optional[str] = Field(
        default=None,
        description="Directory where the output files will be saved. If None, defaults to ../../output.",
    )

    @field_validator("data")
    @classmethod
    def safe_data(cls, data):
        if not isinstance(data, (dict, list)):
            raise ValueError("Data must be a dict or list of dicts.")
        return data


class GenerateStructuredDataChartTool(BaseTool):
    """Tool to generate a structured data chart from time series data."""

    name: str = "generate_structured_data_chart"
    description: str = "Generates a structured data chart from time series JSON data."
    args_schema: Type[BaseModel] = GenerateStructuredDataChartArgs

    def _run(
        self,
        data,
        chart_title,
        template_name="ipca.json.j2",
        template_dir=None,
        output_dir=None,
        chart_file_name=None,
    ) -> str:

        # Set up Jinja2 environment and render Vega-Lite spec
        if template_dir is None:
            template_dir = os.path.join(os.getcwd(), "templates", "charts")

        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_name)
        vega_spec_str = template.render(
            data=json.dumps(data),
            chart_title=chart_title,
        )

        # Set output directory
        if output_dir is None:
            output_dir = os.path.join(os.getcwd(), "output")
        if chart_file_name is None:
            chart_file_name = chart_title.replace(" ", "_")

        # Export to PNG using vl-convert-python
        image_file = os.path.join(output_dir, f"{chart_file_name}.png")
        try:
            png_data = vlc.vegalite_to_png(vega_spec_str)
            with open(image_file, "wb") as imgf:
                imgf.write(png_data)

            return image_file

        except Exception as e:
            raise RuntimeError(f"Failed to export Vega-Lite chart to PNG: {e}")
