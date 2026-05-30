import os
import sys

try:
    from groq import Groq
except ImportError:
    print("❌ Библиотека groq не найдена! Выполните: pip install groq")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
except ImportError:
    print("❌ Библиотека rich не найдена! Выполните: pip install rich")
    sys.exit(1)

# --- НАСТРОЙКА МОДЕЛИ ---
MODEL_NAME = "llama-3.3-70b-versatile"

IGNORE_DIRS = {'.git', '__pycache__', 'node_modules', 'venv', '.venv', '.idea', '.vscode', 'dist', 'build', 'target'}
IGNORE_FILES = {'README.md', '.DS_Store', 'groq_readme_gen.py'}

console = Console()

def get_api_key():
    key_path = os.path.expanduser("~/.groq_readme_key")
    if os.environ.get("GROQ_API_KEY"):
        return os.environ.get("GROQ_API_KEY")
        
    if os.path.exists(key_path):
        console.print("\n[bold yellow]🔑 Нашелся сохраненный ключ.[/]")
        console.print("[cyan]1.[/] Оставить его")
        console.print("[cyan]2.[/] Ввести новый")
        choice = input("\nВыбирай (1-2) [1]: ").strip() or "1"
        if choice == "1":
            with open(key_path, "r", encoding="utf-8") as f:
                return f.read().strip()
                
    api_key = input("🔑 Вставь API-ключ Groq: ").strip()
    if api_key:
        try:
            with open(key_path, "w", encoding="utf-8") as f:
                f.write(api_key)
            console.print("[bold green]💾 Сохранил.[/]")
        except Exception:
            pass
    return api_key

def detect_license(project_path):
    try:
        for item in os.listdir(project_path):
            if item.lower() in ["license", "license.txt", "license.md"]:
                with open(os.path.join(project_path, item), "r", encoding="utf-8", errors="ignore") as f:
                    first_lines = [f.readline().strip() for _ in range(3)]
                    clean_lines = [line for line in first_lines if line]
                    return " | ".join(clean_lines)[:100]
    except Exception:
        pass
    return " shadow "

def generate_tree(dir_path, base_path, prefix=""):
    tree = []
    try:
        entries = sorted(os.listdir(dir_path))
    except Exception:
        return tree

    entries = [e for e in entries if e not in IGNORE_DIRS and e not in IGNORE_FILES]
    
    for i, entry in enumerate(entries):
        path = os.path.join(dir_path, entry)
        is_last = (i == len(entries) - 1)
        connector = "└── " if is_last else "├── "
        
        if os.path.isdir(path):
            tree.append(f"{prefix}{connector}📁 {entry}/")
            new_prefix = prefix + ("    " if is_last else "│   ")
            tree.extend(generate_tree(path, base_path, new_prefix))
        else:
            tree.append(f"{prefix}{connector}📄 {entry}")
            
    return tree

def get_important_context(project_path):
    context = ""
    config_files = {
        'requirements.txt', 'package.json', 'go.mod', 'Cargo.toml', 
        'CMakeLists.txt', 'Makefile', 'Dockerfile', 'docker-compose.yml',
        'build.gradle', 'pom.xml', 'mix.exs'
    }
    source_extensions = {
        '.py', '.js', '.jsx', '.ts', '.tsx', '.c', '.cpp', '.cc', '.h', '.hpp',
        '.rs', '.go', '.java', '.cs', '.sh', '.rb', '.php', '.asm', '.s', '.lua', 
        '.kt', '.dart', '.swift', '.ex', '.exs'
    }
    
    file_count = 0
    max_files = 25

    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for filename in files:
            if filename in IGNORE_FILES:
                continue
            ext = os.path.splitext(filename)[1].lower()
            if filename in config_files or ext in source_extensions:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, project_path)
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = "".join(f.readlines()[:60])
                        context += f"\n--- Содержимое файла: {rel_path} ---\n{content}\n"
                        file_count += 1
                except Exception:
                    pass
            if file_count >= max_files:
                break
        if file_count >= max_files:
            break
    return context

def choose_tone():
    console.print("\n[bold magenta]🎭 В каком стиле пишем?[/]")
    console.print("[cyan]1.[/] Нормальный человеческий [dim](живой язык)[/]")
    console.print("[cyan]2.[/] Сухие факты [dim](коротко, только техническая суть)[/]")
    console.print("[cyan]3.[/] Подробный разбор [dim](детально разжевать структуру)[/]")
    console.print("[cyan]4.[/] Строгий [dim](официальный инженерный стиль)[/]")
    console.print("[cyan]5.[/] Свои условия [dim](кастомные рамки)[/]")
    
    choice = input("\nТвой вариант (1-5) [1]: ").strip() or "1"
    if choice == "1":
        return "ТРЕБОВАНИЕ К ОБЪЕМУ И СТИЛЮ: Естественный, живой язык разработчика. Пиши просто, уверенно и по делу. Стандартный объем."
    elif choice == "2":
        return "ТРЕБОВАНИЕ К ОБЪЕМУ И СТИЛЮ: Максимально лаконичный стиль. Меньше слов, больше дела. Только ключевые технические факты, ужимай объем."
    elif choice == "3":
        return "ТРЕБОВАНИЕ К ОБЪЕМУ И СТИЛЮ: Глубокий технический разбор. Детально опиши назначение модулей и логику взаимодействия."
    elif choice == "4":
        return "ТРЕБОВАНИЕ К ОБЪЕМУ И СТИЛЮ: Академический технический стиль. Идеальная терминология, строгость и структурированность."
    elif choice == "5":
        custom = input("\n👉 Что именно нужно? (например: 'строго в две строки', 'минимум текста'): ").strip()
        return f"ЖЕСТКОЕ ОГРАНИЧЕНИЕ ОБЪЕМА И СТИЛЯ ОТ ПОЛЬЗОВАТЕЛЯ: {custom}."
    return "ТРЕБОВАНИЕ К ОБЪЕМУ И СТИЛЮ: Естественный язык разработчика."

def choose_language():
    console.print("\n[bold magenta]🌐 Какой язык нужен?[/]")
    console.print("[cyan]1.[/] Украинский")
    console.print("[cyan]2.[/] Русский")
    console.print("[cyan]3.[/] Английский")
    console.print("[cyan]4.[/] Другой (ввести руками)")
    
    choice = input("\nВыбирай цифру (1-4) [3]: ").strip() or "3"
    if choice == "1": return "Украинский"
    if choice == "2": return "Русский"
    if choice == "3": return "Английский"
    if choice == "4": return input("\n👉 Напиши язык: ").strip()
    return "Английский"

def choose_emoji_preference():
    console.print("\n[bold magenta]✨ Добавляем эмодзи?[/]")
    console.print("[cyan]1.[/] Да, аккуратно по кодексу [dim](точечно для навигации)[/]")
    console.print("[cyan]2.[/] Нет, строго чистый текст [dim](вообще без смайликов)[/]")
    
    choice = input("\nТвой выбор (1-2) [1]: ").strip() or "1"
    if choice == "1":
        return """ ТРЕБОВАНИЕ К ВИЗУАЛЬНОЙ НАВИГАЦИИ (ОБЯЗАТЕЛЬНЫЕ ЭМОДЗИ):
    - Ты ОБЯЗАН добавить ровно по одному техническому эмодзи в начале каждого крупного заголовка (строк с # или ##) и основных пунктов списков, чтобы улучшить читаемость разметки.
    - Подбирай смайлики строго по техническому смыслу контекста:
      * `⚙️` или `🛠️` — сборка, компиляция, настройка конфигурации.
      * `📦` — зависимости, пакеты, модули репозитория.
      * `⌨️` или `💻` — консольные команды, флаги запуска, использование в терминале.
      * `🔒` — шифрование, безопасность, приватность данных.
      * `📡` или `🌐` — сеть, сокеты, трафик, API-запросы.
      * `🧠` или `🎯` — логика работы программы, ключевые алгоритмы.
      * `⚠️` или `🛑` — важные предупреждения, лимиты, варнинги.
      * `📄` или `📁` — файлы исходного кода, структура директорий.
    - Категорически запрещено использовать бессмысленный "маркетинговый спам" вроде `✨`, `🔥`, `🚀`, `🎉`."""
    else:
        return " КАТЕГОРИЧЕСКИЙ ЗАПРЕТ НА ЭМОДЗИ: Не используй абсолютно никакие смайлики, иконки или эмодзи в тексте. Выдавай строго чистый текст и стандартную Markdown-разметку."

def main():
    console.print(Panel.fit("[bold reverse green]   readmeGEN helper  [/]", border_style="green"))
    
    api_key = get_api_key()
    if not api_key:
        console.print("[bold red]❌ Без ключа работать не буду.[/]")
        return

    project_path = input("\n📁 Путь к папке проекта: ").strip()
    project_path = os.path.abspath(os.path.expanduser(project_path))
    
    if not os.path.exists(project_path) or not os.path.isdir(project_path):
        console.print(f"[bold red]❌ Нет такой папки: '{project_path}'[/]")
        return

    selected_tone = choose_tone()
    selected_lang = choose_language()
    emoji_rule = choose_emoji_preference()

    console.print(f"\n[yellow]👀 Проверяю файлы в {project_path}...[/]")
    
    project_name = os.path.basename(project_path)
    tree_lines = [f"📁 {project_name}/"] + generate_tree(project_path, project_path)
    project_tree = "\n".join(tree_lines)
    code_context = get_important_context(project_path)
    license_info = detect_license(project_path)
    
    author = input("\n👤 Твой ник на GitHub (если нужен в тексте): ").strip() or "developer"

    prompt = f"""
    ВНИМАНИЕ! КРИТИЧЕСКИЙ ИГРАЮЩИЙ ПРИОРИТЕТ №1 (ПРАВИЛО ФОРМАТА):
    {selected_tone}
    Если в этом правиле указано жесткое ограничение по размеру (например: "в две строки", "коротко в один абзац", "без разделов"), ты ОБЯЗАН полностью проигнорировать любые требования к структуре, анализу, модулям и схемам ниже. Выдай ровно тот объем и формат, который затребован в этом пункте, не создавая лишнего текста.

    ---
    
    Ты — ведущий системный инженер и контрибьютор в ядро Linux. Твоя задача — составить README.md для репозитория '{project_name}'.
    
     КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО:
    - Использовать стандартные маркетинговые шаблоны, клише вроде "быстрый/эффективный/простой" и генерировать одинаковую структуру для разных проектов.
    
     ИНЖЕНЕРНЫЙ ПОДХОД К АНАЛИЗУ (Выполнять ТОЛЬКО если это не противоречит ПРИОРИТЕТУ №1):
    1. Определи реальную природу проекта (CLI-утилита, системный демон, библиотека, парсер, сетевой инструмент).
    2. Выстрой структуру README на основе специфики кода. Если это CLI — начни сразу с флагов запуска. Если библиотека — с API.
    3. Вместо абстрактных описаний объясни, КАК программа работает внутри под капотом (главный цикл обработки, ключевые алгоритмы).
    4. Если логика сложная, нарисуй небольшую схему передачи данных прямо в ASCII-графике.

    {emoji_rule}
    
    ---

    Исходные данные для анализа:
    Автор: {author}
    Лицензия: {license_info}
    Дерево проекта:
    ```text
    {project_tree}
    ```
    Контекст файлов и исходный код:
    {code_context}
    
    ---
    
    ВЫВОД: Выведи ИСКЛЮЧИТЕЛЬНО валидный Markdown. Никакой воды и мета-текста от себя.
    Язык документа: {selected_lang}.
    
     ФИНАЛЬНАЯ ПРОВЕРКА НА ПРИОРИТЕТ №1:
    Проверь, соответствует ли твой ответ требованию: "{selected_tone}". Если тебя просили написать в две строки или сделать супер-коротко — удали из ответа всё лишнее, включая схемы, заголовки и дерево проекта. Оставь только запрошенный формат.
    """

    messages = [{"role": "user", "content": prompt}]
    
    try:
        client = Groq(api_key=api_key)
        
        while True:
            with console.status("[bold green]🧠 readmeGEN думает...[/]", spinner="bouncingBar"):
                completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    temperature=0.25,  # Чуть-чуть подняли для лучшего следования креативным правилам разметки
                    max_tokens=4000
                )
            
            readme_content = completion.choices[0].message.content
            
            console.print("\n" + "="*40 + " ПОЛУЧЕННЫЙ ВАРИАНТ " + "="*40, style="bold yellow")
            console.print(Markdown(readme_content))
            console.print("=" * 99 + "\n", style="bold yellow")
            
            console.print("[bold magenta]Что делаем?[/]")
            console.print("[cyan]1.[/] Отлично, сохраняй")
            console.print("[cyan]2.[/] Надо доработать (напишу замечания)")
            
            action = input("\nТвой выбор (1-2) [1]: ").strip() or "1"
            
            if action == "1":
                output_file = os.path.join(project_path, "README.md")
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(readme_content)
                console.print(f"\n[bold green]💾 Всё готово, файл записан: {output_file}[/]")
                break
                
            elif action == "2":
                feedback = input("\n👉 Что именно исправить или добавить? ").strip()
                if not feedback:
                    console.print("[bold red]Напиши хоть что-то, чтобы я понял задачу.[/]")
                    continue
                
                messages.append({"role": "assistant", "content": readme_content})
                messages.append({
                    "role": "user", 
                    "content": f"Переделай текст с учетом этого фидбека: {feedback}. Снова верни СТРОГО только Markdown на языке {selected_lang}. Соблюдай рамки объема."
                })
            else:
                console.print("[bold red]Нет такого варианта, давай еще раз.[/]")
                
    except Exception as e:
        console.print(f"\n[bold red]❌ Ошибка API: {e}[/]")

if __name__ == "__main__":
    main()
