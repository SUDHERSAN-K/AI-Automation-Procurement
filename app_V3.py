import os
import pandas as pd
from shiny import App, ui, render, reactive
from shiny.types import FileInfo
import asyncio
from pathlib import Path
import tempfile
import json
import markdown
from datetime import datetime
import traceback
import io

# Import workflow functions from the v2 file
from workflow_functions_v2 import (
    create_item_vendor_mapping_final,
    generate_recommended_specs,
    generate_scoped_items,
    generate_scope_document_from_csv,
    execute_complete_workflow
)

class WorkflowProcessor:
    """Processes procurement workflow using integrated functions"""
    
    def __init__(self):
        self.working_dir = os.getcwd()
        self.temp_dir = tempfile.mkdtemp()
    
    async def process_files_and_generate_scope(self, items_file, historical_file, project_file, vendors_file, prompt):
        """Execute complete workflow using integrated functions"""
        
        try:
            # Step 1: Copy uploaded files to working directory with standard names
            items_path = os.path.join(self.working_dir, "items.csv")
            historical_path = os.path.join(self.working_dir, "historical_df_items.csv")
            project_path = os.path.join(self.working_dir, "project_rules.md")
            vendors_path = os.path.join(self.working_dir, "vendors.csv")
            
            # Copy uploaded files
            import shutil
            shutil.copy2(items_file, items_path)
            shutil.copy2(historical_file, historical_path)
            shutil.copy2(project_file, project_path)
            shutil.copy2(vendors_file, vendors_path)
            
            # Step 2: Execute complete workflow
            workflow_result = await execute_complete_workflow(
                items_path=items_path,
                historical_path=historical_path,
                vendors_path=vendors_path,
                project_path=project_path
            )
            
            # Step 3: Generate AI-enhanced scope document
            scope_content = await self._generate_enhanced_scope_document(
                workflow_result, project_path, prompt
            )
            
            return {
                "raw_content": scope_content,
                "html_content": markdown.markdown(scope_content or "", extensions=['tables', 'fenced_code']),
                "timestamp": datetime.now().isoformat(),
                "workflow_data": workflow_result,  # Store complete workflow result
                "files_processed": {
                    "items": len(pd.read_csv(items_path)),
                    "vendors": len(pd.read_csv(vendors_path)),
                    "historical_records": len(pd.read_csv(historical_path))
                }
            }
            
        except Exception as e:
            print(f"Workflow processing error: {str(e)}")
            print(traceback.format_exc())
            raise Exception(f"Workflow processing failed: {str(e)}")
    
    async def _generate_enhanced_scope_document(self, workflow_data, project_file, user_prompt):
        """Generate enhanced scope document using OpenAI"""
        
        try:
            from openai import OpenAI
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Read project rules
            with open(project_file, 'r', encoding='utf-8') as f:
                project_content = f.read()
            
            # Prepare workflow data summary
            workflow_summary = self._prepare_workflow_summary(workflow_data)
            
            system_prompt = """You are a senior procurement specialist at Bechtel Corporation. 
            Create a comprehensive, professional procurement scope document that includes:
            
            1. Executive Summary
            2. Project Overview  
            3. Scope of Work
            4. Item Specifications and Vendor Recommendations (MUST include ALL items from the processed data in a complete table)
            5. Delivery Timeline and Requirements
            6. Quality Standards and Certifications
            7. Risk Assessment and Mitigation
            8. Procurement Strategy and Next Steps
            
            CRITICAL REQUIREMENT: In section 4, you must create a complete table that includes EVERY SINGLE ITEM from the processed workflow data. Do not summarize or sample - include all items with their specifications, recommended vendors, regions, contacts, and lead times.
            
            Format the output in professional markdown with tables, bullet points, and clear sections.
            Use the processed workflow data to provide specific vendor recommendations and specifications."""
            
            user_content = f"""
            Based on the following processed procurement workflow data, please {user_prompt}
            
            PROJECT CONTEXT:
            {project_content[:2000]}
            
            PROCESSED WORKFLOW DATA:
            {workflow_summary}
            
            Generate a comprehensive procurement scope document that incorporates all the processed vendor mappings, 
            specifications, and recommendations from the automated workflow analysis.
            """
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=10000,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            return f"Error generating AI-enhanced content: {str(e)}\n\nWorkflow Summary:\n{self._prepare_workflow_summary(workflow_data)}"
    
    def _prepare_workflow_summary(self, workflow_data):
        """Prepare formatted summary of workflow data"""
        
        if not workflow_data:
            return "No workflow data available"
        
        summary_parts = []
        
        # Basic statistics
        if "summary" in workflow_data:
            summary = workflow_data["summary"]
            summary_parts.append(f"""
            WORKFLOW STATISTICS:
            - Items Processed: {summary.get('total_items', 'N/A')}
            - Vendor Mappings: {summary.get('vendor_mappings', 'N/A')}
            - Specifications Generated: {summary.get('specs_generated', 'N/A')}
            - Final Scope Items: {summary.get('final_items', 'N/A')}
            """)
        
        # Include ALL processed items data
        if "scoped_items" in workflow_data and len(workflow_data["scoped_items"]) > 0:
            df_all_items = pd.DataFrame(workflow_data["scoped_items"])
            summary_parts.append(f"""
            ALL PROCESSED ITEMS FOR SCOPE DOCUMENT:
            {df_all_items.to_string(max_cols=10, max_rows=None)}
            """)
        
        return "\n".join(summary_parts) if summary_parts else "Workflow completed successfully"

# Initialize processor
workflow_processor = WorkflowProcessor()

# UI Definition
app_ui = ui.page_fluid(
    ui.include_css("style.css"),
    
    # Header
    ui.div(
        ui.h1("Bechtel Procurement Scope Generator", class_="main-title"),
        ui.p("Advanced AI-powered scope generation with integrated workflow processing", class_="subtitle"),
        class_="header-section"
    ),
    
    # Main content area
    ui.row(
        # Left panel - File uploads
        ui.column(6,
            ui.div(
                ui.h3("File Upload", class_="section-title"),
                
                # File upload cards
                ui.div(
                    ui.div(
                        ui.h5("Items File (items.csv)"),
                        ui.p("Bill of Materials with item specifications", class_="file-description"),
                        ui.input_file("items_file", "Choose items.csv", accept=".csv", multiple=False),
                        ui.output_text("items_status"),
                        class_="upload-card"
                    ),
                    
                    ui.div(
                        ui.h5("Historical Data (historical_df_items.csv)"),
                        ui.p("Historical procurement data for specification recommendations", class_="file-description"),
                        ui.input_file("historical_file", "Choose historical_df_items.csv", accept=".csv", multiple=False),
                        ui.output_text("historical_status"),
                        class_="upload-card"
                    ),
                    
                    ui.div(
                        ui.h5("Project Rules (project_rules.md)"),
                        ui.p("Project-specific procurement rules and constraints", class_="file-description"),
                        ui.input_file("project_file", "Choose project_rules.md", accept=".md", multiple=False),
                        ui.output_text("project_status"),
                        class_="upload-card"
                    ),
                    
                    ui.div(
                        ui.h5("Vendors Database (vendors.csv)"),
                        ui.p("Vendor master list with capabilities and certifications", class_="file-description"),
                        ui.input_file("vendors_file", "Choose vendors.csv", accept=".csv", multiple=False),
                        ui.output_text("vendors_status"),
                        class_="upload-card"
                    ),
                    class_="upload-grid"
                ),
                class_="upload-section"
            )
        ),
        
        # Right panel - Prompt and generation
        ui.column(6,
            ui.div(
                ui.h3("Scope Generation", class_="section-title"),
                
                ui.div(
                    ui.input_text_area(
                        "prompt_input",
                        "Enter your scope generation requirements:",
                        placeholder="Example: Generate a comprehensive procurement scope for renewable energy infrastructure components. Include detailed vendor justifications, risk analysis, and delivery timeline considerations for a Middle East solar facility project.",
                        rows=8,
                        width="100%"
                    ),
                    class_="prompt-section"
                ),
                
                ui.div(
                    ui.input_action_button("generate_btn", "Generate Scope Document", class_="btn-generate"),
                    ui.br(),
                    ui.output_text("generation_status"),
                    class_="action-section"
                ),
                
                ui.div(
                    ui.output_ui("workflow_summary"),
                    class_="workflow-summary"
                ),
                
                ui.div(
                    ui.output_ui("download_section"),
                    class_="download-section"
                ),
                
                class_="generation-section"
            )
        )
    ),
    
    # Results section
    ui.div(
        ui.output_ui("results_section"),
        class_="results-container"
    ),
    
    # Footer
    ui.div(
        ui.p("Bechtel Corporation | Advanced Procurement Intelligence System", class_="footer-text"),
        class_="footer-section"
    )
)

def server(input, output, session):
    # Reactive values
    uploaded_files = reactive.Value({})
    generated_content = reactive.Value(None)
    processing_status = reactive.Value("")
    
    # File upload handlers
    @reactive.Effect
    @reactive.event(input.items_file)
    def handle_items_upload():
        if input.items_file():
            file_info = input.items_file()[0]
            files = uploaded_files.get().copy()
            files["items"] = file_info["datapath"]
            uploaded_files.set(files)
    
    @reactive.Effect
    @reactive.event(input.historical_file)
    def handle_historical_upload():
        if input.historical_file():
            file_info = input.historical_file()[0]
            files = uploaded_files.get().copy()
            files["historical"] = file_info["datapath"]
            uploaded_files.set(files)
    
    @reactive.Effect
    @reactive.event(input.project_file)
    def handle_project_upload():
        if input.project_file():
            file_info = input.project_file()[0]
            files = uploaded_files.get().copy()
            files["project"] = file_info["datapath"]
            uploaded_files.set(files)
    
    @reactive.Effect
    @reactive.event(input.vendors_file)
    def handle_vendors_upload():
        if input.vendors_file():
            file_info = input.vendors_file()[0]
            files = uploaded_files.get().copy()
            files["vendors"] = file_info["datapath"]
            uploaded_files.set(files)
    
    # Status outputs
    @output
    @render.text
    def items_status():
        files = uploaded_files.get()
        if "items" in files:
            try:
                df = pd.read_csv(files["items"])
                return f"✅ Uploaded: {len(df)} items"
            except:
                return "❌ Error reading file"
        return "📁 No file selected"
    
    @output
    @render.text
    def historical_status():
        files = uploaded_files.get()
        if "historical" in files:
            try:
                df = pd.read_csv(files["historical"])
                return f"✅ Uploaded: {len(df)} historical records"
            except:
                return "❌ Error reading file"
        return "📁 No file selected"
    
    @output
    @render.text
    def project_status():
        files = uploaded_files.get()
        if "project" in files:
            try:
                with open(files["project"], 'r') as f:
                    content = f.read()
                return f"✅ Uploaded: {len(content)} characters"
            except:
                return "❌ Error reading file"
        return "📁 No file selected"
    
    @output
    @render.text
    def vendors_status():
        files = uploaded_files.get()
        if "vendors" in files:
            try:
                df = pd.read_csv(files["vendors"])
                return f"✅ Uploaded: {len(df)} vendors"
            except:
                return "❌ Error reading file"
        return "📁 No file selected"
    
    @output
    @render.text
    def generation_status():
        return processing_status.get()
    
    # Main generation handler
    @reactive.Effect
    @reactive.event(input.generate_btn)
    async def handle_generation():
        files = uploaded_files.get()
        prompt = input.prompt_input()
        
        # Validate inputs
        if not all(key in files for key in ["items", "historical", "project", "vendors"]):
            processing_status.set("❌ Please upload all required files")
            return
        
        if not prompt.strip():
            processing_status.set("❌ Please enter a scope generation prompt")
            return
        
        try:
            processing_status.set("🔄 Processing files and generating scope...")
            
            # Process workflow and generate content
            result = await workflow_processor.process_files_and_generate_scope(
                files["items"], files["historical"], files["project"], files["vendors"], prompt
            )
            
            generated_content.set(result)
            processing_status.set("✅ Scope document generated successfully!")
            
        except Exception as e:
            processing_status.set(f"❌ Error: {str(e)}")
            print(f"Generation error: {traceback.format_exc()}")
    
    # Workflow summary display
    @output
    @render.ui
    def workflow_summary():
        content = generated_content.get()
        if not content:
            return ui.div()
        
        workflow_data = content.get("workflow_data", {})
        files_data = content.get("files_processed", {})
        
        return ui.div(
            ui.h4("Workflow Summary", style="color: #2c5aa0; margin-bottom: 15px;"),
            ui.div(
                ui.p(f"📊 Items Processed: {files_data.get('items', 'N/A')}", style="margin: 5px 0;"),
                ui.p(f"🏢 Vendors Available: {files_data.get('vendors', 'N/A')}", style="margin: 5px 0;"),
                ui.p(f"📚 Historical Records: {files_data.get('historical_records', 'N/A')}", style="margin: 5px 0;"),
                ui.p(f"🎯 Generated: {content.get('timestamp', 'N/A')}", style="margin: 5px 0;"),
                style="background: #f0f4f8; padding: 15px; border-radius: 8px; border-left: 4px solid #ff6b35;"
            )
        )
    
    # Download section
    @output
    @render.ui
    def download_section():
        content = generated_content.get()
        if not content:
            return ui.div()
        
        return ui.div(
            ui.h4("Download Options", style="color: #ff6b35; margin-bottom: 15px;"),
            ui.div(
                ui.download_button(
                    "download_markdown",
                    "Download Markdown",
                    style="background: #ff6b35; color: white; border: none; padding: 10px 20px; margin: 5px; border-radius: 5px; cursor: pointer;"
                ),
                ui.download_button(
                    "download_html",
                    "Download HTML", 
                    style="background: #ff6b35; color: white; border: none; padding: 10px 20px; margin: 5px; border-radius: 5px; cursor: pointer;"
                ),
                ui.download_button(
                    "download_csv",
                    "Download Final Scoped Items CSV", 
                    style="background: #2c5aa0; color: white; border: none; padding: 10px 20px; margin: 5px; border-radius: 5px; cursor: pointer;"
                ),
                style="background: #f0f4f8; padding: 15px; border-radius: 8px; border-left: 4px solid #ff6b35;"
            )
        )
    
    # Download handlers
    @render.download(filename="scope_document.md")
    def download_markdown():
        content = generated_content.get()
        if content and content.get("raw_content"):
            return io.StringIO(content["raw_content"])
        else:
            return io.StringIO("No content available for download")
    
    @render.download(filename="scope_document.html")
    def download_html():
        content = generated_content.get()
        if content and content.get("html_content"):
            html_template = f"""<!DOCTYPE html>
<html>
<head>
    <title>Procurement Scope Document</title>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3 {{ color: #2c5aa0; }}
        table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f0f4f8; }}
        .generated-time {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="generated-time">Generated: {content.get('timestamp', '')}</div>
    {content["html_content"]}
</body>
</html>"""
            return io.StringIO(html_template)
        else:
            return io.StringIO("<html><body><h1>No content available for download</h1></body></html>")
    
    @render.download(filename="scoped_items.csv")
    def download_csv():
        content = generated_content.get()
        if content and content.get("workflow_data"):
            # Check if scoped_items.csv exists in the working directory
            csv_file_path = "scoped_items.csv"
            if os.path.exists(csv_file_path):
                with open(csv_file_path, 'r', encoding='utf-8') as f:
                    return io.StringIO(f.read())
            else:
                # Fallback: create CSV from workflow data if file doesn't exist
                workflow_data = content.get("workflow_data", {})
                if "scoped_items" in workflow_data:
                    import pandas as pd
                    df = pd.DataFrame(workflow_data["scoped_items"])
                    csv_content = df.to_csv(index=False)
                    return io.StringIO(csv_content)
                else:
                    return io.StringIO("Item Name,Final Specification,Recommended Vendor,Vendor Region,Vendor Contact,Vendor Email,Lead Time (days),Vendor Certifications,Similarity Score\nNo scoped items data available")
        else:
            return io.StringIO("Item Name,Final Specification,Recommended Vendor,Vendor Region,Vendor Contact,Vendor Email,Lead Time (days),Vendor Certifications,Similarity Score\nNo content available for download")
    
    # Results display
    @output
    @render.ui
    def results_section():
        content = generated_content.get()
        if not content:
            return ui.div()
        
        return ui.div(
            ui.h2("Generated Scope Document", class_="results-title"),
            ui.div(
                ui.HTML(content.get("html_content", "")),
                class_="results-content"
            ),
            class_="results-section"
        )

# Create the app
app = App(app_ui, server)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
