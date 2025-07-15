import os
import numpy as np
import pandas as pd
import json
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import asyncio

def create_item_vendor_mapping_final(df_items, df_vendors, tfidf_threshold=0.5):
    """
    Create final item-vendor mapping using TF-IDF similarity
    """
    try:
        # Prepare text for TF-IDF analysis
        item_texts = []
        for _, item in df_items.iterrows():
            text = f"{item.get('Item Name', '')} {item.get('Specification', '')}"
            item_texts.append(text.lower())
        
        vendor_texts = []
        for _, vendor in df_vendors.iterrows():
            text = f"{vendor.get('Expertise', '')} {vendor.get('Certifications', '')}"
            vendor_texts.append(text.lower())
        
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        all_texts = item_texts + vendor_texts
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        
        # Calculate similarity between items and vendors
        item_vectors = tfidf_matrix[:len(item_texts)]
        vendor_vectors = tfidf_matrix[len(item_texts):]
        similarity_matrix = cosine_similarity(item_vectors, vendor_vectors)
        
        # Create mappings
        mappings = []
        for i, (_, item) in enumerate(df_items.iterrows()):
            similarities = similarity_matrix[i]
            best_vendor_idx = np.argmax(similarities)
            best_similarity = similarities[best_vendor_idx]
            
            # Include all items, but mark low similarity ones
            vendor = df_vendors.iloc[best_vendor_idx]
            mappings.append({
                'Item Name': item.get('Item Name', ''),
                'Item Specification': item.get('Specification', ''),
                'Recommended Vendor': vendor.get('Vendor Name', '') if best_similarity >= tfidf_threshold else 'No optimal match found',
                'Vendor Region': vendor.get('Region', '') if best_similarity >= tfidf_threshold else 'TBD',
                'Vendor Contact': vendor.get('Contact Name', '') if best_similarity >= tfidf_threshold else 'TBD',
                'Vendor Email': vendor.get('Contact Email', '') if best_similarity >= tfidf_threshold else 'TBD',
                'Vendor Lead Time': vendor.get('Avg Lead Time (days)', 0) if best_similarity >= tfidf_threshold else 0,
                'Similarity Score': round(best_similarity, 3),
                'Vendor Expertise': vendor.get('Expertise', '') if best_similarity >= tfidf_threshold else 'Manual review required',
                'Vendor Certifications': vendor.get('Certifications', '') if best_similarity >= tfidf_threshold else 'Manual review required'
            })
        
        print(f"Created {len(mappings)} item-vendor mappings")
        return mappings
        
    except Exception as e:
        print(f"Error in item-vendor mapping: {str(e)}")
        return []

def generate_recommended_specs(items_path, historical_path):
    """
    Generate recommended specifications based on historical data
    """
    try:
        df_items = pd.read_csv(items_path)
        df_historical = pd.read_csv(historical_path)
        
        spec_recommendations = []
        
        for _, item in df_items.iterrows():
            item_name = item.get('Item Name', '')
            current_spec = item.get('Specification', '')
            
            # Find historical matches
            historical_matches = df_historical[
                df_historical['Item Name'].str.contains(item_name, case=False, na=False)
            ]
            
            if len(historical_matches) > 0:
                # Get most common specification
                spec_counts = historical_matches['Specification'].value_counts()
                recommended_spec = spec_counts.index[0] if len(spec_counts) > 0 else current_spec
                confidence = spec_counts.iloc[0] / len(historical_matches) if len(spec_counts) > 0 else 0.5
            else:
                recommended_spec = current_spec
                confidence = 0.3
            
            spec_recommendations.append({
                'Item Name': item_name,
                'Current Specification': current_spec,
                'Recommended Specification': recommended_spec,
                'Confidence Score': round(confidence, 3),
                'Historical Matches': len(historical_matches)
            })
        
        print(f"Generated {len(spec_recommendations)} specification recommendations")
        return spec_recommendations
        
    except Exception as e:
        print(f"Error in specification generation: {str(e)}")
        return []

def generate_scoped_items():
    """
    Generate scoped items by combining mappings and specifications
    """
    try:
        # Check if required CSV files exist
        mapping_file = "item_vendor_mapping_final.csv"
        specs_file = "recommended_specs.csv"
        
        scoped_items = []
        
        if os.path.exists(mapping_file) and os.path.exists(specs_file):
            df_mapping = pd.read_csv(mapping_file)
            df_specs = pd.read_csv(specs_file)
            
            # Merge mappings with specifications
            for _, mapping in df_mapping.iterrows():
                item_name = mapping.get('Item Name', '')
                
                # Find corresponding specification
                spec_match = df_specs[df_specs['Item Name'] == item_name]
                if len(spec_match) > 0:
                    spec_rec = spec_match.iloc[0]
                    recommended_spec = spec_rec.get('Recommended Specification', mapping.get('Item Specification', ''))
                else:
                    recommended_spec = mapping.get('Item Specification', '')
                
                scoped_items.append({
                    'Item Name': item_name,
                    'Final Specification': recommended_spec,
                    'Recommended Vendor': mapping.get('Recommended Vendor', ''),
                    'Vendor Region': mapping.get('Vendor Region', ''),
                    'Vendor Contact': mapping.get('Vendor Contact', ''),
                    'Vendor Email': mapping.get('Vendor Email', ''),
                    'Lead Time (days)': mapping.get('Vendor Lead Time', 0),
                    'Vendor Certifications': mapping.get('Vendor Certifications', ''),
                    'Similarity Score': mapping.get('Similarity Score', 0)
                })
        
        print(f"Generated {len(scoped_items)} scoped items")
        return scoped_items
        
    except Exception as e:
        print(f"Error in scoped items generation: {str(e)}")
        return []

def generate_scope_document_from_csv():
    """
    Generate final scope document from CSV data
    """
    try:
        scoped_file = "scoped_items.csv"
        
        if os.path.exists(scoped_file):
            df_scoped = pd.read_csv(scoped_file)
            
            # Convert to list of dictionaries for easier processing
            scope_document = df_scoped.to_dict('records')
            
            print(f"Generated scope document with {len(scope_document)} items")
            return scope_document
        else:
            print("Scoped items file not found, generating empty scope")
            return []
            
    except Exception as e:
        print(f"Error in scope document generation: {str(e)}")
        return []

async def execute_complete_workflow(items_path, historical_path, vendors_path, project_path):
    """
    Execute the complete procurement workflow
    """
    try:
        print("Starting complete workflow execution...")
        
        # Step 1: Load data
        df_items = pd.read_csv(items_path)
        df_vendors = pd.read_csv(vendors_path)
        df_historical = pd.read_csv(historical_path)
        
        print(f"Loaded {len(df_items)} items, {len(df_vendors)} vendors, {len(df_historical)} historical records")
        
        # Step 2: Create item-vendor mappings
        mappings = create_item_vendor_mapping_final(df_items, df_vendors, tfidf_threshold=0.1)
        
        # Save mappings to CSV
        if mappings:
            df_mappings = pd.DataFrame(mappings)
            df_mappings.to_csv("item_vendor_mapping_final.csv", index=False)
        
        # Step 3: Generate recommended specifications
        spec_recommendations = generate_recommended_specs(items_path, historical_path)
        
        # Save specifications to CSV
        if spec_recommendations:
            df_specs = pd.DataFrame(spec_recommendations)
            df_specs.to_csv("recommended_specs.csv", index=False)
        
        # Step 4: Generate scoped items
        scoped_items = generate_scoped_items()
        
        # Save scoped items to CSV
        if scoped_items:
            df_scoped = pd.DataFrame(scoped_items)
            df_scoped.to_csv("scoped_items.csv", index=False)
        
        # Step 5: Generate final scope document
        final_scope = generate_scope_document_from_csv()
        
        # Prepare summary
        workflow_summary = {
            "total_items": len(df_items),
            "vendor_mappings": len(mappings),
            "specs_generated": len(spec_recommendations),
            "final_items": len(final_scope),
            "completion_time": datetime.now().isoformat()
        }
        
        result = {
            "mappings": mappings,
            "specifications": spec_recommendations,
            "scoped_items": scoped_items,
            "final_scope": final_scope,
            "summary": workflow_summary
        }
        
        print("Workflow execution completed successfully")
        return result
        
    except Exception as e:
        print(f"Error in complete workflow execution: {str(e)}")
        raise Exception(f"Workflow execution failed: {str(e)}")

# Utility functions for data validation
def validate_csv_file(file_path, required_columns):
    """
    Validate CSV file has required columns
    """
    try:
        df = pd.read_csv(file_path)
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        return True, f"File validated successfully with {len(df)} rows"
    
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def get_workflow_status():
    """
    Get current workflow status based on existing files
    """
    files_status = {
        "items.csv": os.path.exists("items.csv"),
        "vendors.csv": os.path.exists("vendors.csv"),
        "historical_df_items.csv": os.path.exists("historical_df_items.csv"),
        "project_rules.md": os.path.exists("project_rules.md"),
        "item_vendor_mapping_final.csv": os.path.exists("item_vendor_mapping_final.csv"),
        "recommended_specs.csv": os.path.exists("recommended_specs.csv"),
        "scoped_items.csv": os.path.exists("scoped_items.csv")
    }
    
    return files_status

# Additional helper functions for enhanced functionality
def calculate_cost_estimates(scoped_items, cost_factors=None):
    """
    Calculate cost estimates for scoped items
    """
    if not cost_factors:
        cost_factors = {
            "base_cost_per_item": 1000,
            "region_multipliers": {
                "USA": 1.2,
                "Europe": 1.1,
                "Asia": 0.9,
                "Middle East": 1.0
            }
        }
    
    try:
        for item in scoped_items:
            base_cost = cost_factors["base_cost_per_item"]
            region = item.get("Vendor Region", "Unknown")
            
            # Apply region multiplier
            multiplier = 1.0
            for region_key, mult in cost_factors["region_multipliers"].items():
                if region_key.lower() in region.lower():
                    multiplier = mult
                    break
            
            estimated_cost = base_cost * multiplier
            item["Estimated_Cost_USD"] = round(estimated_cost, 2)
        
        return scoped_items
    
    except Exception as e:
        print(f"Error calculating cost estimates: {str(e)}")
        return scoped_items

def generate_risk_assessment(scoped_items):
    """
    Generate risk assessment for scoped items
    """
    try:
        for item in scoped_items:
            lead_time = item.get("Lead Time (days)", 30)
            similarity_score = item.get("Similarity Score", 0.5)
            
            # Calculate risk factors
            time_risk = "High" if lead_time > 60 else "Medium" if lead_time > 30 else "Low"
            vendor_risk = "Low" if similarity_score > 0.7 else "Medium" if similarity_score > 0.4 else "High"
            
            overall_risk = "High" if time_risk == "High" or vendor_risk == "High" else "Medium" if time_risk == "Medium" or vendor_risk == "Medium" else "Low"
            
            item["Time_Risk"] = time_risk
            item["Vendor_Risk"] = vendor_risk
            item["Overall_Risk"] = overall_risk
        
        return scoped_items
    
    except Exception as e:
        print(f"Error generating risk assessment: {str(e)}")
        return scoped_items

def export_to_multiple_formats(data, base_filename="scope_document"):
    """
    Export data to multiple formats (CSV, JSON, Excel)
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        exports = {}
        
        # Convert to DataFrame if it's a list
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data
        
        # CSV export
        csv_filename = f"{base_filename}_{timestamp}.csv"
        df.to_csv(csv_filename, index=False)
        exports["csv"] = csv_filename
        
        # JSON export
        json_filename = f"{base_filename}_{timestamp}.json"
        df.to_json(json_filename, orient='records', indent=2)
        exports["json"] = json_filename
        
        # Excel export
        excel_filename = f"{base_filename}_{timestamp}.xlsx"
        df.to_excel(excel_filename, index=False)
        exports["excel"] = excel_filename
        
        return exports
        
    except Exception as e:
        print(f"Error exporting to multiple formats: {str(e)}")
        return {}
