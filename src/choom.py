import subprocess
import argparse
import time
import os
import argcomplete
import pathlib
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.table import Table
from rich_argparse.contrib import ParagraphRichHelpFormatter # type: ignore
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def print_banner(console):
    padding = '  '
    
    C = [[' ', '┌', '─', '┐'], [' ', '│', ' ', ' '], [' ', '└', '─', '┘']]
    H = [[' ', '┬', ' ', '┬'], [' ', '├', '─', '┤'], [' ', '┴', ' ', '┴']]
    O = [[' ', '┌', '─', '┐'], [' ', '│', ' ', '│'], [' ', '└', '─', '┘']]
    O2 = [[' ', '┌', '─', '┐'], [' ', '│', ' ', '│'], [' ', '└', '─', '┘']]
    M = [[' ', '┬', ' ', ' ', '┬'], [' ', '│', '┬', '┬', '│'], [' ', '┴', ' ', ' ', '┴']]
    
    banner = [C, H, O, O2, M]

    for row in range(3):
        line = padding
        for letter in banner:
            line += ''.join(letter[row]) + '  '
        console.print(f"[bold bright_green]{line}[/bold bright_green]")

def main():
    console = Console()

    # Parse arguments
    parser = argparse.ArgumentParser(
        description='CH00M by MaxMnMl (v0.22)',
        formatter_class=ParagraphRichHelpFormatter,
        epilog='Examples:\n\n'
           '  python3 choom.py -u https://example.com -d 5 -rl 200\n\n'
           '  python3 choom.py -f urls.txt -ua "CustomUserAgent" -c "sessionid=abc123"\n\n'
           '  python3 choom.py --no-crawl --path /path/to/directory'
)
    parser.add_argument('-f', '--url-file', type=str, help='Path to the URL file list.')
    parser.add_argument('-u', '--url', type=str, help='Single URL to process.')
    parser.add_argument('-rl', '--rate-limit', type=int, default=150, help='Maximum requests to send per second (default=150).')
    parser.add_argument('-cr', '--concurrency', type=int, default=10, help='Number of concurrent fetchers to use (default=10).')
    parser.add_argument('-ua', '--custom-ua', type=str, help='Custom User-Agent header value.')
    parser.add_argument('-c', '--cookie', type=str, help='Cookie header value for authenticated crawling.')
    parser.add_argument('-s', '--silent', action='store_true', help='Disable ASCII art display.')
    parser.add_argument('-d', '--depth', type=str, default=3, help='Maximum depth to crawl (default=3).')
    parser.add_argument('-hl', '--headless', action='store_true', help='Enable headless hybrid crawling.')
    parser.add_argument('-sd', '--include-subs', action='store_true', help='Include subdomains of the target domain in the crawling process.')
    parser.add_argument('-js', '--js-secrets', action='store_true', help='Run SecretFinder on JS files.')
    parser.add_argument('-dd', '--disco-doc', action='store_true', help='Discover interesting documents(jpg,png,pdf).')
    parser.add_argument('--no-crawl', action='store_true', help='Bypass the crawling step.')
    parser.add_argument('--path', type=str, help='If no-crawl option enabled, Path to the directory containing endpointsJs.txt and endpoints.txt.')
    parser.add_argument('-p', '--proxy', type=str, help='http proxy to use (eg http://127.0.0.1:8080).')
    parser.add_argument('-n', '--notify', action='store_true', help='Send a notification when the workflow is done.')
    args = parser.parse_args()

    # Enable argcomplete
    argcomplete.autocomplete(parser)

    # Set User-Agent header based on user input
    ua_header = f"-H 'User-Agent: {args.custom_ua}'" if args.custom_ua else ""

    # Set Cookie header based on user input
    cookie = f"-H 'Cookie: {args.cookie}'" if args.cookie else ""

    # Set Proxy based on user input
    proxy = f"-proxy '{args.proxy}'" if args.proxy else ""

    # Set script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Display ASCII art if not in silent mode
    if not args.silent:
        print_banner(console)
        console.print("[bold magenta]        by MaxMnMl (Version 0.22)[/bold magenta]\n")

    if args.no_crawl:
        if not args.path:
            console.print("[red]You must provide the input directory with --path containing endpointsJs.txt and endpoints.txt files [/red]")
            return
        new_content_dir = args.path
    else:

        # Create content directory if it doesn't exist
        if not os.path.exists('content'):
            os.makedirs('content')

        # Determine the next subdirectory number
        subdirs = [d for d in os.listdir('content') if os.path.isdir(os.path.join('content', d))]
        next_subdir = str(len(subdirs) + 1).zfill(2)
        new_content_dir = os.path.join('content', next_subdir)
        os.makedirs(new_content_dir)
  
        # Subdomain Enumeration
        subdomains = []
        if args.url_file:
            console.rule("[bold bright_green]Subdomain Enumeration[/bold bright_green]")
            alive_path = os.path.join(new_content_dir, "alive.txt")
            subdomains_txt = os.path.join(new_content_dir, "subdomains.txt")
            with open(args.url_file, "r") as f:
                domains = [line.strip() for line in f if line.strip()]
            for domain in domains:
                console.print(f"[yellow]Enumerating subdomains for: {domain}[/yellow]")
                sub1 = os.path.join(new_content_dir, f"sub1_{domain}.txt")
                sub2 = os.path.join(new_content_dir, f"sub2_{domain}.txt")
                allsub = os.path.join(new_content_dir, f"allsub_{domain}.txt")
                # subfinder
                console.print(f"[blue]subfinder -silent -d {domain} -o {sub1}[/blue]")
                try:
                    subprocess.run(f"subfinder -silent -d {domain} -o {sub1}", shell=True, check=True)
                except KeyboardInterrupt:
                    console.print("[red]Subdomain enumeration interrupted by user, moving to next step.[/red]")
                # assetfinder
                console.print(f"[blue]assetfinder --subs-only {domain} | tee {sub2}[/blue]")
                try:
                    subprocess.run(f"assetfinder --subs-only {domain} | tee {sub2}", shell=True, check=True)
                except KeyboardInterrupt:
                    console.print("[red]Subdomain enumeration interrupted by user, moving to next step.[/red]")
                # Ensure each file exists (otherwise, create an empty one)
                for f in [sub1, sub2]:
                    if not os.path.exists(f):
                        pathlib.Path(f).touch()
                # merge
                try:
                    subprocess.run(f"cat {sub1} {sub2} > {allsub}", shell=True, check=True)
                except KeyboardInterrupt:
                    console.print("[red]Subdomain enumeration by user, moving to next step.[/red]")
                os.remove(sub1)
                os.remove(sub2)
                # deduplicate
                try:
                    subprocess.run(f"cat {allsub} | anew >> {subdomains_txt}", shell=True, check=True)
                except KeyboardInterrupt:
                    console.print("[red]Subdomain enumeration interrupted by user, moving to next step.[/red]")
                os.remove(allsub)
            console.print(f"\n[green]Looking for alive subdomains[/green]")
            console.print(f"[blue]httpx -silent -l {subdomains_txt} -o {alive_path}[/blue]")
            try:
                subprocess.run(f"httpx -silent -l {subdomains_txt} -o {alive_path}", shell=True, check=True)
            except KeyboardInterrupt:
                console.print("[red]Subdomain enumeration interrupted by user, moving to next step.[/red]")
            os.remove(subdomains_txt)
            # Use alive.txt as subdomains list
            with open(alive_path, "r") as f:
                subdomains = [line.strip() for line in f if line.strip()]
        elif args.url:
            console.rule("[bold bright_green]Subdomain Enumeration[/bold bright_green]")
            domain = args.url.strip()
            sub1 = os.path.join(new_content_dir, "sub1.txt")
            sub2 = os.path.join(new_content_dir, "sub2.txt")
            sub3 = os.path.join(new_content_dir, "sub3.txt")
            allsub = os.path.join(new_content_dir, "allsub.txt")
            subdomains_txt = os.path.join(new_content_dir, "subdomains.txt")
            alive_path = os.path.join(new_content_dir, "alive.txt")
            console.print(f"[blue]subfinder -silent -d {domain} -o {sub1}[/blue]")
            try:
                subprocess.run(f"subfinder -silent -d {domain} -o {sub1}", shell=True, check=True)
            except KeyboardInterrupt:
                console.print("[red]Subdomain enumeration interrupted by user, moving to next step.[/red]")
            try:
                subprocess.run(f"amass enum --passive -d {domain} -o {sub2}", shell=True, check=True)
            except KeyboardInterrupt:
                console.print("[red]Subdomain enumeration interrupted by user, moving to next step.[/red]")
            console.print(f"[blue]assetfinder --subs-only {domain} | tee {sub3}[/blue]")
            try:
                subprocess.run(f"assetfinder --subs-only {domain} | tee {sub3}", shell=True, check=True)
            except KeyboardInterrupt:
                console.print("[red]Subdomain enumeration interrupted by user, moving to next step.[/red]")
            # S'assurer que chaque fichier existe (sinon, le créer vide)
            for f in [sub1, sub2, sub3]:
                if not os.path.exists(f):
                    pathlib.Path(f).touch()
            try:
                subprocess.run(f"cat {sub1} {sub2} {sub3} > {allsub}", shell=True, check=True)
            except KeyboardInterrupt:
                console.print("[red]Subdomain enumeration interrupted by user, moving to next step.[/red]")
            os.remove(sub1)
            os.remove(sub2)
            os.remove(sub3)
            try:
                subprocess.run(f"cat {allsub} | anew >> {subdomains_txt}", shell=True, check=True)
            except KeyboardInterrupt:
                console.print("[red]Subdomain enumeration interrupted by user, moving to next step.[/red]")
            os.remove(allsub)
            console.print(f"\n[green]Looking for alive subdomains[/green]")
            console.print(f"[blue]httpx -silent -l {subdomains_txt} -o {alive_path}[/blue]")
            try:
                subprocess.run(f"httpx -silent -l {subdomains_txt} -o {alive_path}", shell=True, check=True)
            except KeyboardInterrupt:
                console.print("[red]Subdomain enumeration interrupted by user, moving to next step.[/red]")
            os.remove(subdomains_txt)
            with open(alive_path, "r") as f:
                subdomains = [line.strip() for line in f if line.strip()]
        else:
            console.print("[red]You must provide either a subdomain file with -f or a single URL with -u[/red]")
            return
        
        # Set waybackurls options based on user input
        waybackurls_options = "" if args.include_subs else "-no-subs"

        # Set katana/cariddi options based on user input
        headless_options = "-hl -noi -nos" if args.headless else ""
        concurrency_options = f"-c {args.concurrency}" if args.concurrency else ""

        # Wayback Crawling
        console.rule("[bold bright_green]Wayback Crawling[/bold bright_green]")
        for subdomain in subdomains:
            subdomain = subdomain.strip()
            if not subdomain:
                continue
            console.print(f"[yellow]Processing subdomain: {subdomain}[/yellow]")

            waybackurls_cmd = f"waybackurls {subdomain} {waybackurls_options} | tee {new_content_dir}/crawl.txt"
            console.print(f"[blue]Running command: {waybackurls_cmd}[/blue]")

            try:
                subprocess.run(waybackurls_cmd, shell=True, check=True)
            except KeyboardInterrupt:
                console.print("[red]Crawling interrupted by user[/red]")

        # Gau Crawling
        console.rule("[bold bright_green]Gau Crawling[/bold bright_green]")
        for subdomain in subdomains:
            subdomain = subdomain.strip()
            if not subdomain:
                continue
            console.print(f"[yellow]Processing subdomain: {subdomain}[/yellow]")

            gau_cmd = f"gau {subdomain} | tee {new_content_dir}/crawl.txt"
            console.print(f"[blue]Running command: {gau_cmd}[/blue]")

            try:
                subprocess.run(gau_cmd, shell=True, check=True)
            except KeyboardInterrupt:
                console.print("[red]Crawling interrupted by user[/red]")

        # Katana Crawling
        console.rule("[bold bright_green]Katana Crawling[/bold bright_green]")
        for subdomain in subdomains:
            subdomain = subdomain.strip()
            if not subdomain:
                continue

            console.print(f"[yellow]Processing subdomain: {subdomain}[/yellow]")

            katana_cmd = f"katana -silent -u {subdomain} -jc -jsl -kf all -fs fqdn -fx -rl {args.rate_limit} -d {args.depth} {concurrency_options} {headless_options} {ua_header} {cookie} | tee -a {new_content_dir}/crawl.txt"
            console.print(f"[blue]Running command: {katana_cmd}[/blue]")
            
            try:
                subprocess.run(katana_cmd, shell=True, check=True)
            except KeyboardInterrupt:
                console.print("[red]Crawling interrupted by user[/red]")

        # Cariddi Crawling
        console.rule("[bold bright_green]Cariddi Crawling[/bold bright_green]")
        for subdomain in subdomains:
            subdomain = subdomain.strip()
            if not subdomain:
                continue

            console.print(f"[yellow]Processing subdomain: {subdomain}[/yellow]")

            ua_cariddi=""
            if args.custom_ua:
                    ua_cariddi=(f"-ua '{args.custom_ua}'")
            cookie_cariddi=""
            if args.cookie:
                    cookie_cariddi=(f"-headers 'Cookie: {args.cookie}'")

            cariddi_cmd = f"echo {subdomain} | cariddi -info -s -err -e -ext 1 -ot cariddi.txt {concurrency_options} {ua_cariddi} {cookie_cariddi} | tee -a {new_content_dir}/crawl.txt"
            console.print(f"[blue]Running command: {cariddi_cmd}[/blue]")
            
            try:
                subprocess.run(cariddi_cmd, shell=True, check=True)
            except KeyboardInterrupt:
                console.print("[red]Crawling interrupted by user[/red]")

        # Move Cariddi output to new content directory
        cariddi_output_dir = 'output-cariddi'
        if os.path.exists(cariddi_output_dir):
            new_cariddi_output_dir = os.path.join(new_content_dir, cariddi_output_dir)
            os.rename(cariddi_output_dir, new_cariddi_output_dir)
        else:
            console.print(f"[red]Cariddi output directory not found: {cariddi_output_dir}[/red]")

        # Virustotal Crawling
        console.rule("[bold bright_green]Virustotal Crawling[/bold bright_green]")
        for i, subdomain in enumerate(subdomains):
            subdomain = subdomain.strip()
            if not subdomain:
                continue

            console.print(f"[yellow]Processing subdomain: {subdomain}[/yellow]")
            virustotalx_script = os.path.join(script_dir, 'script', 'virustotalx.sh')
            virustotalx_cmd = f"/bin/bash {virustotalx_script} {subdomain} | tee -a {new_content_dir}/crawl.txt"
            console.print(f"[blue]Running command: {virustotalx_cmd}[/blue]")
            
            try:
                subprocess.run(virustotalx_cmd, shell=True, check=True)      
            except KeyboardInterrupt:
                console.print("[red]Crawling interrupted by user[/red]")

        # Wait for 20 seconds with a countdown timer if not the last subdomain
            if i < len(subdomains) - 1:
                console.print("[green]Waiting for 20 seconds before the next command...[green]")
                try:
                    with Live(console=console, refresh_per_second=1) as live:
                        for remaining in range(20, 0, -1):
                            table = Table.grid()
                            table.add_column(justify="center", ratio=1)
                            table.add_row(f"[cyan]{remaining} seconds remaining...[cyan]")
                            live.update(table)
                            time.sleep(1)
                except KeyboardInterrupt:
                    console.print("[red]Countdown interrupted by user. Moving to the next command.[/red]")

        console.print("\n[bold green]Crawling Done !!![bold /green]")

        # Filter .js files from endpoints.txt
        console.print("\n[green]Filtering .js files ...[green]")
        filter_js_cmd = (
            f"grep '.js$' {new_content_dir}/crawl.txt | "
            f"grep -v 'jquery' | "
            f"grep -v 'bootstrap' | "
            f"grep -v 'api.google.com' | "
            f"grep -v 'google-analytics' | "
            f"sort | uniq "
            f"| httpx -silent -mc 200,301,302 -rl {args.rate_limit} {ua_header} {cookie} "
            f"> {new_content_dir}/endpointsJs.txt"
        )
        with console.status("[bold green]Running command...[/bold green]", spinner="dots"):
            subprocess.run(filter_js_cmd, shell=True, check=True)
        
        # Clean up endpoints.txt
        console.print("[green]Cleaning up endpoints...[green]")
        cleanup_cmd = f"grep '^http' {new_content_dir}/crawl.txt | sort | uniq | httpx -silent -fc 404 -fr -rl {args.rate_limit} {ua_header} {cookie} {proxy} > {new_content_dir}/endpoints.txt"
        console.print(f"[blue]Running command: {cleanup_cmd}[/blue]")
        with console.status("[bold green]Running command...[/bold green]", spinner="dots"):
            subprocess.run(cleanup_cmd, shell=True, check=True)
        
    # Discover secrets in JS files
    if args.js_secrets:
        console.rule("[bold bright_green]Possible secrets in JS files [SecretFinder][/bold bright_green]")
        with open(f"{new_content_dir}/resultJS.txt", "a") as result_file:
            result_file.write("\033[1;34m################## SECRETS IN JS FILES [SecretFinder] ###################\033[0m\n")
            result_file.write(" \n")
        with open(f"{new_content_dir}/endpointsJs.txt", "r") as file:
            for url in file:
                url = url.strip()
                if url:
                    console.print(f"[yellow]Processing URL: {url}[/yellow]")
                    headers = ""
                    if args.cookie:
                        headers = f"-c '{args.cookie}'"
                    secret_finder_script = os.path.join(script_dir, 'script', 'SecretFinder.py')
                    discover_cmd = f"python3 {secret_finder_script} -i {url} -o cli {headers} | tee -a {new_content_dir}/resultJS.txt"
                    console.print(f"[blue]Running command: {discover_cmd}[/blue]")
                    try:
                        subprocess.run(discover_cmd, shell=True, check=True, timeout=60)
                    except subprocess.TimeoutExpired:
                        console.print(f"[red]Timeout expired for URL: {url}[/red]")
    
    # Discover Backup files
    console.rule("[bold bright_green]Possible backup files[/bold bright_green]")
    with open(f"{new_content_dir}/result.txt", "a") as result_file:
        result_file.write(" \n")
        result_file.write("\033[1;34m################## BACKUP FILES ###################\033[0m\n")
        result_file.write(" \n")
    extensions01 = ['.zip', '.rar', '.7z', '.exe', '.tar', '.gz', '.dll', '.iso', '.bk', '.bak', '.old']
    discover_cmd = f"grep -E '({'|'.join(extensions01)})$' {new_content_dir}/endpoints.txt | tee -a {new_content_dir}/result.txt"
    console.print(f"[blue]Running command: {discover_cmd}[/blue]")
    subprocess.run(discover_cmd, shell=True, check=True)

    # Discover Interesting Files
    console.rule("[bold bright_green]Possible interesting files[/bold bright_green]")
    with open(f"{new_content_dir}/result.txt", "a") as result_file:
        result_file.write(" \n")
        result_file.write("\033[1;34m################## INTERESTING FILES ###################\033[0m\n")
        result_file.write(" \n")
    extensions03 = ['.aspx', '.ashx', '.cgi', '.jsp', '.xml', '.txt', '.xhtml']
    discover_cmd = f"grep -E '({'|'.join(extensions03)})$' {new_content_dir}/endpoints.txt | tee -a {new_content_dir}/result.txt"
    console.print(f"[blue]Running command: {discover_cmd}[/blue]")
    subprocess.run(discover_cmd, shell=True, check=True)
    
    # Discover Interesting Information
    console.rule("[bold bright_green]Possible interesting information[/bold bright_green]")
    with open(f"{new_content_dir}/result.txt", "a") as result_file:
        result_file.write(" \n")
        result_file.write("\033[1;34m################## INTERESTING INFORMATIONS ###################\033[0m\n")
        result_file.write(" \n")
    extensions02 = ['token=', 'apikey=', '/resetpassword/', 'registration', 'login', '==', 'password', 'secret', 'api', 'pass', 'username', 'user', 'admin', 'code=', 'cred']
    discover_cmd = f"grep -E '({'|'.join(extensions02)})' {new_content_dir}/endpoints.txt | tee -a {new_content_dir}/result.txt"
    console.print(f"[blue]Running command: {discover_cmd}[/blue]")
    subprocess.run(discover_cmd, shell=True, check=True)
    
    # Discover GraphQL endpoints
    console.rule("[bold bright_green]Possible graphQL Api[/bold bright_green]")
    with open(f"{new_content_dir}/result.txt", "a") as result_file:
        result_file.write(" \n")
        result_file.write("\033[1;34m################## GRAPHQL API ###################\033[0m\n")
        result_file.write(" \n")
    extensions03 = ['query', 'mutation', 'graphql', 'graphiql', 'subscriptions', 'graph', 'playground' , 'altair', 'explorer', 'voyager']
    discover_cmd = f"grep -E '({'|'.join(extensions03)})$' {new_content_dir}/endpoints.txt | tee -a {new_content_dir}/result.txt"
    console.print(f"[blue]Running command: {discover_cmd}[/blue]")
    subprocess.run(discover_cmd, shell=True, check=True)
    
    # Discover Interesting Document (Financial Program Only:-dd)
    if args.disco_doc:
        console.rule("[bold bright_green]Possible interesting documents[/bold bright_green]")
        with open(f"{new_content_dir}/result.txt", "a") as result_file:
            result_file.write(" \n")
            result_file.write("\033[1;34m################## INTERESTING DOCUMENTS ###################\033[0m\n")
            result_file.write(" \n")
        extensions04 = ['.jpg', '.png', '.pdf']
        discover_cmd = f"grep -E '({'|'.join(extensions04)})$' {new_content_dir}/endpoints.txt | tee -a {new_content_dir}/result.txt"
        console.print(f"[blue]Running command: {discover_cmd}[/blue]")
        subprocess.run(discover_cmd, shell=True, check=True)
    
    # Filters 403 Forbidden endpoints 
    console.print("\n[green]Filters 403 Forbidden endpoints...[green]")
    cleanup_cmd2 = f"cat {new_content_dir}/endpoints.txt | httpx -silent -fc 403 -fr -rl {args.rate_limit} {ua_header} {cookie} > {new_content_dir}/endpoints_filtered.txt"
    with console.status("[bold green]Running command...[/bold green]", spinner="dots"):
        subprocess.run(cleanup_cmd2, shell=True, check=True)
    
    # Remove duplicate query string with uro
    console.print("[green]Removing duplicate query string...[green]")
    cleanup_cmd3 = f"cat {new_content_dir}/endpoints_filtered.txt | uro >> {new_content_dir}/endpoints_param.txt"
    with console.status("[bold green]Running command...[/bold green]", spinner="dots"):
        subprocess.run(cleanup_cmd3, shell=True, check=True)
    
    # Use gf to find vulnerabilities
    console.rule(f"[bold bright_green]Possible vulnerable parameters (gf)[/bold bright_green]")
    with open(f"{new_content_dir}/result.txt", "a") as result_file:
        result_file.write(" \n")
        result_file.write("\033[1;34m################## VULNERABLE PARAMETERS ###################\033[0m")
        result_file.write(" \n")
    gf_patterns = ['lfi', 'ssrf', 'rce', 'interestingparams', 'idor', 'xss']
    for pattern in gf_patterns:
        console.print(f"[yellow]#### Hunt {pattern.upper()} ####[/yellow]")
        with open(f"{new_content_dir}/result.txt", "a") as result_file:
            result_file.write(" \n")
            result_file.write("\033[0;33m#### Hunt LFI, SSRF, RCE, INTERESTING, IDOR, XSS ####\033[0m")
            result_file.write(" \n")
        gf_cmd = f"cat {new_content_dir}/endpoints_param.txt | gf {pattern} | tee -a {new_content_dir}/result.txt"
        console.print(f"[blue]Running command: {gf_cmd}[/blue]")
        subprocess.run(gf_cmd, shell=True, check=True)

    # Use kxss on XSS patterns to exploit automatically
    console.rule(f"[bold bright_green]Exploit XSS (kxss)[/bold bright_green]")
    kxss_cmd = f"cat {new_content_dir}/endpoints_param.txt | gf xss | kxss | tee {new_content_dir}/kxss.txt"
    console.print(f"[blue]Running command: {kxss_cmd}[/blue]")
    try:
        subprocess.run(kxss_cmd, shell=True, check=True)
    except KeyboardInterrupt:
        console.print("[red]kxss execution interrupted by user[/red]")
    
    # Use dalfox on XSS patterns to exploit automatically
    console.rule(f"[bold bright_green]Exploit XSS (dalfox)[/bold bright_green]")
    headers = ""
    if args.cookie:
        headers = f"-C '{args.cookie}'"
    dalfox_cmd = f"cat {new_content_dir}/endpoints_param.txt | gf xss | dalfox pipe --worker 50 {headers} -o {new_content_dir}/dalfox.txt --output-all "
    console.print(f"[blue]Running command: {dalfox_cmd}[/blue]")
    try:
        subprocess.run(dalfox_cmd, shell=True, check=True)
    except KeyboardInterrupt:
        console.print("[red]Dalfox execution interrupted by user[/red]")
    
    # Send notification if -n is specified
    if args.notify:
        console.rule(f"[bold bright_green]Notification[/bold bright_green]")
        notify_cmd = 'echo "Choom workflow is done !!!" | notify -silent'
        console.print(f"[blue]Running command: {notify_cmd}[/blue]")
        try:
            subprocess.run(notify_cmd, shell=True, check=True)
        except KeyboardInterrupt:
            console.print("[red]Notification interrupted by user[/red]")

    console.print("\n[bold green]All is Done !!![bold /green]")

if __name__ == "__main__":
    main()

