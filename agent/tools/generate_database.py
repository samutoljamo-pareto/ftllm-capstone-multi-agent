from pydantic import BaseModel
from pydantic_ai import RunContext, Tool
import os
from typing import Dict, Any, List
from agents.sqlite_agent import create_sqlite_agent
from tools.run_sqlite_agent import run_sqlite_agent_and_implement
from pydantic_ai.models.openai import OpenAIModel


async def generate_sqlite_database(
    ctx: RunContext[Dict[str, Any]], 
    put_random_shite: str,
    include_auth: bool = True,
    include_session: bool = True,
    database_name: str = "app.db",

) -> str:
    """
    Generate a SQLite database for the Next.js application.
    
    Args:
        app_description: Description of what the application does and what data it needs
        include_auth: Whether to include authentication features (default: True)
        include_session: Whether to include session management (default: True)
        database_name: Name of the SQLite database file (default: "app.db")
        
    Returns:
        A message describing the result of the database generation
    """

    print("Generating SQLite database...")

    print("random shite", put_random_shite)
    
    # Get project path from context
    project_path = getattr(ctx.deps, 'project_path', None)
    if not project_path:
        return "Failed to generate SQLite database: Project path not available in context"
    
    print("Project path found")

    # Directly scan the pages directory to get a list of pages
    pages = []
    pages_dir = os.path.join(project_path, "pages")
    if os.path.exists(pages_dir):
        for root, _, files in os.walk(pages_dir):
            for file in files:
                if file.endswith(".js") or file.endswith(".tsx") or file.endswith(".jsx"):
                    actual_path = os.path.join(root, file)
                    # Convert to virtual URL
                    relative_path = os.path.relpath(actual_path, pages_dir)
                    virtual_url = f"/{relative_path}"
                    pages.append(virtual_url)
    

    print("reading page contents")
    # Read content of existing pages directly
    file_contents = {}
    for page_path in pages:
        try:
            # Remove leading slash if present
            clean_path = page_path[1:] if page_path.startswith("/") else page_path
            actual_path = os.path.join(project_path, "pages", clean_path)
            
            with open(actual_path, "r", encoding="utf-8") as f:
                content = f.read()
                if content:
                    file_contents[page_path] = content
        except FileNotFoundError:
            # Skip files that don't exist
            continue
    print("page contents read")
    
    # Get AI model from context if available
    ai_model_name = getattr(ctx.deps, 'ai_model_name', None)
    # If ai_model_name is not found, try getting ai_model object
    ai_model_obj = None
    if not ai_model_name:
        ai_model_obj = getattr(ctx.deps, 'ai_model', None) 
        if ai_model_obj and hasattr(ai_model_obj, 'model_name'):
            ai_model_name = ai_model_obj.model_name
        else:
            print("ai model not found")
            return "Failed to generate SQLite database: AI model not available in context"
    
    print(f"Using AI model: {ai_model_name}")
    print("creating sqlite agent")


    ai_model = OpenAIModel(
        model_name=ai_model_name
    )

    # Run the SQLite agent
    sqlite_agent = create_sqlite_agent(ai_model)

    print(sqlite_agent)
    print("running sqlite agent")

    result = await run_sqlite_agent_and_implement(
        sqlite_agent=sqlite_agent,
        app_description=ctx.deps.project_description,
        existing_files=pages,
        file_contents=file_contents,
        include_auth=include_auth,
        include_session=include_session,
        database_name=database_name,
        project_path=project_path,
        context=ctx,
        ai_model=ai_model
    )

    if result.success:
        files_created = "\n- " + "\n- ".join(result.created_files)
        print("sqlite agent run success")
        return f"SQLite database generated successfully. Created files: {files_created}"
    else:
        print("sqlite agent run failed")
        return f"Failed to generate SQLite database: {result.message}"
    

# Create the Tool instance for this function
generate_sqlite_database_tool = Tool(generate_sqlite_database)