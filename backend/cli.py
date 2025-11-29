#!/usr/bin/env python3
"""
TalkDocs2 CLI - Command Line Interface for documentation chatbot
"""
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from typing import Optional, List
import asyncio
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Import backend modules
from crawler import WebCrawler
from vector_store import VectorStore
from rag_chat import RAGChatService

logger = logging.getLogger(__name__)

app = typer.Typer(help="TalkDocs2 CLI - Documentation Chatbot", add_completion=False)
console = Console()

# Global state
vector_store = None
crawler = None
rag_chat = None

def initialize_services():
    """Initialize backend services"""
    global vector_store, crawler, rag_chat
    if vector_store is None:
        vector_store = VectorStore()
        crawler = WebCrawler(
            vector_store=vector_store,
            persistence_workers=3,  # Parallel document storage
            max_concurrent_requests=10,  # Concurrent HTTP requests
            parse_workers=4  # Thread pool for HTML parsing
        )
        rag_chat = RAGChatService(vector_store)
    return vector_store, crawler, rag_chat

async def init_async():
    """Initialize async components"""
    vs, _, _ = initialize_services()
    await vs.initialize()
    
    # If there's an active source but no collection, set it
    if vs.current_source_id and not vs.collection:
        try:
            await vs.set_active_source(vs.current_source_id)
        except Exception as e:
            logger.warning(f"Could not load active source {vs.current_source_id}: {str(e)}")

@app.command()
def crawl(
    url: str = typer.Argument(..., help="URL to crawl"),
    max_depth: int = typer.Option(3, "--depth", "-d", help="Maximum crawl depth"),
    max_pages: int = typer.Option(1000, "--pages", "-p", help="Maximum pages to crawl"),
    delay: float = typer.Option(0.3, "--delay", help="Delay between requests (seconds)")
):
    """Crawl a website and index its content"""
    console.print(f"[bold blue]Starting crawl for:[/bold blue] {url}")
    
    async def do_crawl():
        await init_async()
        vs, cr, _ = initialize_services()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Crawling...", total=None)
            
            try:
                results = await cr.crawl_domain_with_duplicate_check(
                    start_url=url,
                    max_depth=max_depth,
                    max_pages=max_pages,
                    delay=delay
                )
                
                new_pages = results.get('new_pages', [])
                existing_docs = results.get('existing_documents', [])
                
                # Store new pages
                if new_pages:
                    await vs.store_documents(new_pages, source_url=url)
                
                progress.update(task, completed=True)
                
                # Display results
                table = Table(title="Crawl Results", show_header=True, header_style="bold magenta")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                
                table.add_row("New Pages Crawled", str(len(new_pages)))
                table.add_row("Existing Documents", str(len(existing_docs)))
                table.add_row("Total Visited", str(results.get('total_visited', 0)))
                table.add_row("Total Content Length", f"{results.get('total_content_length', 0):,} chars")
                
                console.print(table)
                console.print(f"[bold green]✓ Crawl completed successfully![/bold green]")
                
            except Exception as e:
                console.print(f"[bold red]✗ Crawl failed:[/bold red] {str(e)}")
                raise typer.Exit(1)
    
    asyncio.run(do_crawl())

@app.command()
def chat(
    query: Optional[str] = typer.Argument(None, help="Query to ask"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Start interactive chat mode"),
    source_id: Optional[str] = typer.Option(None, "--source", "-s", help="Source ID to use")
):
    """Chat with the documentation using RAG"""
    async def do_chat():
        await init_async()
        vs, _, rc = initialize_services()
        
        # Set source if provided
        if source_id:
            await vs.set_active_source(source_id)
            console.print(f"[bold blue]Using source:[/bold blue] {source_id}")
        
        if interactive:
            # Interactive mode
            console.print(Panel.fit(
                "[bold cyan]TalkDocs2 Interactive Chat[/bold cyan]\n"
                "Type your questions about the documentation.\n"
                "Type 'exit' or 'quit' to end the session.",
                border_style="blue"
            ))
            
            conversation_history = []
            
            while True:
                try:
                    user_input = Prompt.ask("\n[bold green]You[/bold green]")
                    
                    if user_input.lower() in ['exit', 'quit', 'q']:
                        console.print("[bold yellow]Goodbye![/bold yellow]")
                        break
                    
                    if not user_input.strip():
                        continue
                    
                    console.print("[bold blue]Thinking...[/bold blue]")
                    
                    # Generate response
                    result = await rc.generate_response(
                        user_message=user_input,
                        conversation_history=conversation_history,
                        max_context_docs=10
                    )
                    
                    if result['success']:
                        # Display response
                        console.print("\n[bold cyan]Assistant:[/bold cyan]")
                        console.print(Markdown(result['response']))
                        
                        # Show sources
                        if result.get('sources'):
                            console.print(f"\n[dim]Sources: {len(result['sources'])} documents used[/dim]")
                        
                        # Update conversation history
                        conversation_history.append({'role': 'user', 'content': user_input})
                        conversation_history.append({'role': 'assistant', 'content': result['response']})
                    else:
                        console.print(f"[bold red]Error:[/bold red] {result.get('error', 'Unknown error')}")
                
                except KeyboardInterrupt:
                    console.print("\n[bold yellow]Interrupted. Goodbye![/bold yellow]")
                    break
                except Exception as e:
                    console.print(f"[bold red]Error:[/bold red] {str(e)}")
        else:
            # Single query mode
            if not query:
                console.print("[bold red]Error:[/bold red] Please provide a query or use --interactive mode")
                raise typer.Exit(1)
            
            console.print(f"[bold blue]Query:[/bold blue] {query}\n")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Processing...", total=None)
                
                result = await rc.generate_response(
                    user_message=query,
                    conversation_history=[],
                    max_context_docs=10
                )
                
                progress.update(task, completed=True)
            
            if result['success']:
                console.print("\n[bold cyan]Response:[/bold cyan]")
                console.print(Markdown(result['response']))
                
                if result.get('sources'):
                    console.print(f"\n[dim]Used {len(result['sources'])} documents from the knowledge base[/dim]")
            else:
                console.print(f"[bold red]Error:[/bold red] {result.get('error', 'Unknown error')}")
                raise typer.Exit(1)
    
    asyncio.run(do_chat())

@app.command()
def sources(
    list_all: bool = typer.Option(True, "--list", "-l", help="List all sources"),
    set_active: Optional[str] = typer.Option(None, "--set", "-s", help="Set active source by ID"),
    delete: Optional[str] = typer.Option(None, "--delete", "-d", help="Delete source by ID")
):
    """Manage documentation sources"""
    async def do_sources():
        await init_async()
        vs, _, _ = initialize_services()
        
        if set_active:
            await vs.set_active_source(set_active)
            console.print(f"[bold green]✓ Active source set to:[/bold green] {set_active}")
            return
        
        if delete:
            if Confirm.ask(f"Are you sure you want to delete source '{delete}'?"):
                await vs.delete_source(delete)
                console.print(f"[bold green]✓ Source deleted:[/bold green] {delete}")
            else:
                console.print("[bold yellow]Cancelled[/bold yellow]")
            return
        
        if list_all:
            sources_list = await vs.get_available_sources()
            active_source = vs.current_source_id
            
            if not sources_list:
                console.print("[yellow]No sources found. Use 'crawl' command to add sources.[/yellow]")
                return
            
            table = Table(title="Documentation Sources", show_header=True, header_style="bold magenta")
            table.add_column("Source ID", style="cyan")
            table.add_column("Documents", style="green", justify="right")
            table.add_column("Created", style="yellow")
            table.add_column("Status", style="bold")
            
            for source in sources_list:
                status = "✓ Active" if source['source_id'] == active_source else ""
                table.add_row(
                    source['source_id'],
                    str(source['document_count']),
                    source.get('created_at', 'Unknown')[:10] if source.get('created_at') else 'Unknown',
                    status
                )
            
            console.print(table)
    
    asyncio.run(do_sources())

@app.command()
def provider(
    get: bool = typer.Option(False, "--get", "-g", help="Get current provider"),
    set_provider: Optional[str] = typer.Option(None, "--set", "-s", help="Set provider (lm_studio or gemini)")
):
    """Manage AI model provider"""
    async def do_provider():
        await init_async()
        _, _, rc = initialize_services()
        
        if set_provider:
            if set_provider not in ['lm_studio', 'gemini']:
                console.print("[bold red]Error:[/bold red] Provider must be 'lm_studio' or 'gemini'")
                raise typer.Exit(1)
            
            rc.set_provider(set_provider)
            console.print(f"[bold green]✓ Provider set to:[/bold green] {set_provider}")
            return
        
        if get or (not set_provider):
            provider_type = "Gemini API" if rc.provider == "gemini" else "LM Studio (Local)"
            table = Table(title="Model Provider", show_header=True, header_style="bold magenta")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Provider", rc.provider)
            table.add_row("Type", provider_type)
            table.add_row("Model Name", rc.model_name or "N/A")
            if rc.base_url:
                table.add_row("Base URL", rc.base_url)
            
            console.print(table)
    
    asyncio.run(do_provider())

@app.command()
def stats():
    """Show system statistics"""
    async def do_stats():
        await init_async()
        vs, _, rc = initialize_services()
        
        # Get vector store stats
        vector_stats = await vs.get_stats()
        chat_stats = await rc.get_chat_stats()
        
        table = Table(title="System Statistics", show_header=True, header_style="bold magenta")
        table.add_column("Category", style="cyan")
        table.add_column("Metric", style="yellow")
        table.add_column("Value", style="green")
        
        table.add_row("Vector Store", "Total Documents", str(vector_stats.get('total_documents', 0)))
        table.add_row("Vector Store", "Collection", vector_stats.get('collection_name', 'N/A'))
        
        table.add_row("AI Model", "Provider", chat_stats.get('provider', 'N/A'))
        table.add_row("AI Model", "Type", chat_stats.get('model_type', 'N/A'))
        table.add_row("AI Model", "Model Name", chat_stats.get('model_name', 'N/A'))
        table.add_row("AI Model", "Status", chat_stats.get('service_status', 'N/A'))
        
        console.print(table)
    
    asyncio.run(do_stats())

@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of results"),
    source_id: Optional[str] = typer.Option(None, "--source", "-s", help="Source ID to search")
):
    """Search documents in the knowledge base"""
    async def do_search():
        await init_async()
        vs, _, _ = initialize_services()
        
        results = await vs.search(query, limit=limit, source_id=source_id)
        
        if not results:
            console.print("[yellow]No results found.[/yellow]")
            return
        
        table = Table(title=f"Search Results for: {query}", show_header=True, header_style="bold magenta")
        table.add_column("Rank", style="cyan", justify="right")
        table.add_column("Title", style="green")
        table.add_column("URL", style="blue")
        table.add_column("Similarity", style="yellow", justify="right")
        
        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            title = metadata.get('title', 'Untitled')[:50]
            url = metadata.get('url', 'N/A')[:40]
            similarity = result.get('similarity_score', 0.0)
            
            table.add_row(
                str(i),
                title,
                url,
                f"{similarity:.3f}"
            )
        
        console.print(table)
        console.print(f"\n[dim]Found {len(results)} results[/dim]")
    
    asyncio.run(do_search())

@app.command()
def clear():
    """Clear all documents from the database"""
    if not Confirm.ask("[bold red]Are you sure you want to clear all documents?[/bold red]"):
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    async def do_clear():
        await init_async()
        vs, _, _ = initialize_services()
        await vs.clear_all()
        console.print("[bold green]✓ Database cleared successfully[/bold green]")
    
    asyncio.run(do_clear())

def show_menu():
    """Display the main menu"""
    menu_text = """
[bold cyan]╔═══════════════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║[/bold cyan]           [bold white]TalkDocs2 - Documentation Chatbot[/bold white]           [bold cyan]║[/bold cyan]
[bold cyan]╚═══════════════════════════════════════════════════════════╝[/bold cyan]

[bold yellow]Main Menu:[/bold yellow]

  [bold cyan]1.[/bold cyan]  Chat with Documentation (Interactive)
  [bold cyan]2.[/bold cyan]  Chat with Documentation (Single Query)
  [bold cyan]3.[/bold cyan]  Crawl Website
  [bold cyan]4.[/bold cyan]  Manage Sources
  [bold cyan]5.[/bold cyan]  Search Documents
  [bold cyan]6.[/bold cyan]  Manage AI Provider
  [bold cyan]7.[/bold cyan]  View Statistics
  [bold cyan]8.[/bold cyan]  Clear Database
  [bold cyan]9.[/bold cyan]  Exit

"""
    console.print(menu_text)

async def handle_menu_choice(choice: int):
    """Handle menu choice"""
    if choice == 1:
        # Interactive chat
        await do_interactive_chat()
    elif choice == 2:
        # Single query chat
        query = Prompt.ask("\n[bold green]Enter your question[/bold green]")
        if query:
            await do_single_chat(query)
    elif choice == 3:
        # Crawl website
        await do_interactive_crawl()
    elif choice == 4:
        # Manage sources
        await do_manage_sources()
    elif choice == 5:
        # Search documents
        await do_interactive_search()
    elif choice == 6:
        # Manage provider
        await do_manage_provider()
    elif choice == 7:
        # View stats
        await do_show_stats()
    elif choice == 8:
        # Clear database
        await do_clear_database()
    elif choice == 9:
        # Exit
        console.print("\n[bold yellow]Goodbye![/bold yellow]")
        return False
    else:
        console.print("[bold red]Invalid choice. Please try again.[/bold red]")
    
    return True

async def do_interactive_chat():
    """Interactive chat mode"""
    await init_async()
    vs, _, rc = initialize_services()
    
    # Show active source info
    active_source = vs.current_source_id
    if active_source:
        sources_list = await vs.get_available_sources()
        active_source_info = next((s for s in sources_list if s['source_id'] == active_source), None)
        source_info = f"\n[bold yellow]Active Source:[/bold yellow] {active_source}"
        if active_source_info:
            source_info += f" ({active_source_info['document_count']} documents)"
    else:
        source_info = "\n[bold yellow]Warning:[/bold yellow] No active source set. Use 'Manage Sources' to set one."
    
    console.print(Panel.fit(
        f"[bold cyan]Interactive Chat Mode[/bold cyan]{source_info}\n"
        "Type your questions about the documentation.\n"
        "Type 'back' to return to main menu.",
        border_style="blue"
    ))
    
    if not active_source:
        if not Confirm.ask("\n[bold yellow]Continue without an active source?[/bold yellow]"):
            return
    
    conversation_history = []
    
    while True:
        try:
            user_input = Prompt.ask("\n[bold green]You[/bold green]")
            
            if user_input.lower() in ['back', 'exit', 'quit', 'q']:
                break
            
            if not user_input.strip():
                continue
            
            console.print("[bold blue]Thinking...[/bold blue]")
            
            # Ensure active source is set before searching
            if vs.current_source_id and not vs.collection:
                await vs.set_active_source(vs.current_source_id)
            
            result = await rc.generate_response(
                user_message=user_input,
                conversation_history=conversation_history,
                max_context_docs=10
            )
            
            if result['success']:
                console.print("\n[bold cyan]Assistant:[/bold cyan]")
                console.print(Markdown(result['response']))
                
                if result.get('sources'):
                    console.print(f"\n[dim]Sources: {len(result['sources'])} documents used[/dim]")
                elif result.get('context_documents', 0) == 0:
                    console.print("\n[bold yellow]⚠ Warning:[/bold yellow] No relevant documents found in the knowledge base.")
                    console.print("[dim]Try:[/dim]")
                    console.print("[dim]  - Setting an active source with documents[/dim]")
                    console.print("[dim]  - Using a different query[/dim]")
                    console.print("[dim]  - Crawling more documentation[/dim]")
                
                conversation_history.append({'role': 'user', 'content': user_input})
                conversation_history.append({'role': 'assistant', 'content': result['response']})
            else:
                console.print(f"[bold red]Error:[/bold red] {result.get('error', 'Unknown error')}")
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")

async def do_single_chat(query: str):
    """Single query chat"""
    await init_async()
    _, _, rc = initialize_services()
    
    console.print(f"[bold blue]Query:[/bold blue] {query}\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Processing...", total=None)
        
        result = await rc.generate_response(
            user_message=query,
            conversation_history=[],
            max_context_docs=10
        )
        
        progress.update(task, completed=True)
    
    if result['success']:
        console.print("\n[bold cyan]Response:[/bold cyan]")
        console.print(Markdown(result['response']))
        
        if result.get('sources'):
            console.print(f"\n[dim]Used {len(result['sources'])} documents from the knowledge base[/dim]")
    else:
        console.print(f"[bold red]Error:[/bold red] {result.get('error', 'Unknown error')}")
    
    Prompt.ask("\n[dim]Press Enter to continue...[/dim]", default="")

async def do_interactive_crawl():
    """Interactive crawl"""
    url = Prompt.ask("\n[bold green]Enter URL to crawl[/bold green]")
    if not url:
        return
    
    max_depth = IntPrompt.ask("[bold green]Max depth[/bold green]", default=3)
    max_pages = IntPrompt.ask("[bold green]Max pages[/bold green]", default=1000)
    delay = float(Prompt.ask("[bold green]Delay (seconds)[/bold green]", default="0.3"))
    
    await init_async()
    vs, cr, _ = initialize_services()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Crawling...", total=None)
        
        try:
            results = await cr.crawl_domain_with_duplicate_check(
                start_url=url,
                max_depth=max_depth,
                max_pages=max_pages,
                delay=delay
            )
            
            new_pages = results.get('new_pages', [])
            existing_docs = results.get('existing_documents', [])
            
            if new_pages:
                await vs.store_documents(new_pages, source_url=url)
            
            progress.update(task, completed=True)
            
            table = Table(title="Crawl Results", show_header=True, header_style="bold magenta")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("New Pages Crawled", str(len(new_pages)))
            table.add_row("Existing Documents", str(len(existing_docs)))
            table.add_row("Total Visited", str(results.get('total_visited', 0)))
            
            console.print(table)
            console.print(f"[bold green]✓ Crawl completed successfully![/bold green]")
            
        except Exception as e:
            console.print(f"[bold red]✗ Crawl failed:[/bold red] {str(e)}")
    
    Prompt.ask("\n[dim]Press Enter to continue...[/dim]", default="")

async def do_manage_sources():
    """Manage sources interactively"""
    await init_async()
    vs, _, _ = initialize_services()
    
    while True:
        console.print("\n[bold yellow]Sources Management:[/bold yellow]")
        console.print("  1. List all sources")
        console.print("  2. Set active source")
        console.print("  3. Delete source")
        console.print("  4. Back to main menu")
        
        choice = Prompt.ask("\n[bold green]Choose an option[/bold green]", default="1")
        
        if choice == "1":
            sources_list = await vs.get_available_sources()
            active_source = vs.current_source_id
            
            if not sources_list:
                console.print("[yellow]No sources found.[/yellow]")
            else:
                table = Table(title="Documentation Sources", show_header=True, header_style="bold magenta")
                table.add_column("Source ID", style="cyan")
                table.add_column("Documents", style="green", justify="right")
                table.add_column("Created", style="yellow")
                table.add_column("Status", style="bold")
                
                for source in sources_list:
                    status = "✓ Active" if source['source_id'] == active_source else ""
                    table.add_row(
                        source['source_id'],
                        str(source['document_count']),
                        source.get('created_at', 'Unknown')[:10] if source.get('created_at') else 'Unknown',
                        status
                    )
                
                console.print(table)
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]", default="")
        
        elif choice == "2":
            source_id = Prompt.ask("[bold green]Enter source ID[/bold green]")
            if source_id:
                await vs.set_active_source(source_id)
                console.print(f"[bold green]✓ Active source set to:[/bold green] {source_id}")
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]", default="")
        
        elif choice == "3":
            source_id = Prompt.ask("[bold green]Enter source ID to delete[/bold green]")
            if source_id:
                if Confirm.ask(f"Are you sure you want to delete '{source_id}'?"):
                    await vs.delete_source(source_id)
                    console.print(f"[bold green]✓ Source deleted:[/bold green] {source_id}")
                else:
                    console.print("[yellow]Cancelled[/yellow]")
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]", default="")
        
        elif choice == "4":
            break
        else:
            console.print("[bold red]Invalid choice.[/bold red]")

async def do_interactive_search():
    """Interactive search"""
    query = Prompt.ask("\n[bold green]Enter search query[/bold green]")
    if not query:
        return
    
    limit = IntPrompt.ask("[bold green]Number of results[/bold green]", default=10)
    
    await init_async()
    vs, _, _ = initialize_services()
    
    results = await vs.search(query, limit=limit)
    
    if not results:
        console.print("[yellow]No results found.[/yellow]")
    else:
        table = Table(title=f"Search Results for: {query}", show_header=True, header_style="bold magenta")
        table.add_column("Rank", style="cyan", justify="right")
        table.add_column("Title", style="green")
        table.add_column("URL", style="blue")
        table.add_column("Similarity", style="yellow", justify="right")
        
        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            title = metadata.get('title', 'Untitled')[:50]
            url = metadata.get('url', 'N/A')[:40]
            similarity = result.get('similarity_score', 0.0)
            
            table.add_row(str(i), title, url, f"{similarity:.3f}")
        
        console.print(table)
        console.print(f"\n[dim]Found {len(results)} results[/dim]")
    
    Prompt.ask("\n[dim]Press Enter to continue...[/dim]", default="")

async def do_manage_provider():
    """Manage provider interactively"""
    await init_async()
    _, _, rc = initialize_services()
    
    while True:
        console.print("\n[bold yellow]AI Provider Management:[/bold yellow]")
        provider_type = "Gemini API" if rc.provider == "gemini" else "LM Studio (Local)"
        
        table = Table(title="Current Provider", show_header=True, header_style="bold magenta")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Provider", rc.provider)
        table.add_row("Type", provider_type)
        table.add_row("Model Name", rc.model_name or "N/A")
        if rc.base_url:
            table.add_row("Base URL", rc.base_url)
        
        console.print(table)
        
        console.print("\n  1. Switch to LM Studio")
        console.print("  2. Switch to Gemini")
        console.print("  3. Back to main menu")
        
        choice = Prompt.ask("\n[bold green]Choose an option[/bold green]", default="3")
        
        if choice == "1":
            rc.set_provider('lm_studio')
            console.print("[bold green]✓ Provider set to LM Studio[/bold green]")
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]", default="")
        elif choice == "2":
            rc.set_provider('gemini')
            console.print("[bold green]✓ Provider set to Gemini[/bold green]")
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]", default="")
        elif choice == "3":
            break
        else:
            console.print("[bold red]Invalid choice.[/bold red]")

async def do_show_stats():
    """Show statistics"""
    await init_async()
    vs, _, rc = initialize_services()
    
    vector_stats = await vs.get_stats()
    chat_stats = await rc.get_chat_stats()
    
    table = Table(title="System Statistics", show_header=True, header_style="bold magenta")
    table.add_column("Category", style="cyan")
    table.add_column("Metric", style="yellow")
    table.add_column("Value", style="green")
    
    table.add_row("Vector Store", "Total Documents", str(vector_stats.get('total_documents', 0)))
    table.add_row("Vector Store", "Collection", vector_stats.get('collection_name', 'N/A'))
    
    table.add_row("AI Model", "Provider", chat_stats.get('provider', 'N/A'))
    table.add_row("AI Model", "Type", chat_stats.get('model_type', 'N/A'))
    table.add_row("AI Model", "Model Name", chat_stats.get('model_name', 'N/A'))
    table.add_row("AI Model", "Status", chat_stats.get('service_status', 'N/A'))
    
    console.print(table)
    Prompt.ask("\n[dim]Press Enter to continue...[/dim]", default="")

async def do_clear_database():
    """Clear database"""
    if Confirm.ask("\n[bold red]Are you sure you want to clear all documents?[/bold red]"):
        await init_async()
        vs, _, _ = initialize_services()
        await vs.clear_all()
        console.print("[bold green]✓ Database cleared successfully[/bold green]")
    else:
        console.print("[yellow]Cancelled[/yellow]")
    
    Prompt.ask("\n[dim]Press Enter to continue...[/dim]", default="")

async def interactive_mode():
    """Main interactive mode"""
    console.print(Panel.fit(
        "[bold cyan]Welcome to TalkDocs2 CLI[/bold cyan]\n"
        "Initializing services...",
        border_style="blue"
    ))
    
    try:
        await init_async()
        console.print("[bold green]✓ Services initialized[/bold green]\n")
    except Exception as e:
        console.print(f"[bold red]✗ Initialization failed:[/bold red] {str(e)}")
        return
    
    while True:
        try:
            show_menu()
            choice = IntPrompt.ask("\n[bold green]Select an option[/bold green]", default=1)
            
            should_continue = await handle_menu_choice(choice)
            if not should_continue:
                break
            
            console.print()  # Add spacing
            
        except KeyboardInterrupt:
            console.print("\n\n[bold yellow]Goodbye![/bold yellow]")
            break
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]", default="")

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """TalkDocs2 CLI - Documentation Chatbot"""
    # If no command provided, run interactive mode
    if ctx.invoked_subcommand is None:
        asyncio.run(interactive_mode())
    # Otherwise, let typer handle the command

if __name__ == "__main__":
    app()

