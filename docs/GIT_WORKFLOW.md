# Git Workflow

## Branches
- `main`: final submission only.
- `develop`: the default branch where everything is merged.
- Each member works on their own branch: `feature/stt`, `feature/nlp`, `feature/security`, `feature/executor`, `feature/tts`, `feature/linux-ops`, `feature/gui`.

## Steps
1. Get the latest changes: `git checkout develop` then `git pull`
2. Create your branch: `git checkout -b feature/your-module`
3. Work only inside your own folder. Edit other folders only after agreeing with their owner.
4. Save your work: `git add .` then `git commit -m "Clear message"`
5. Push your branch: `git push -u origin feature/your-module`
6. Open a **Pull Request** from your branch into `develop`, and ask a teammate to review it before merging.

## Rules
- Never push directly to `develop` or `main`.
- Never commit the `venv` folder or temporary audio files.
- Write clear commit messages in English.
- Add any new library to `requirements.txt`.
- Agree on the shape of the intent passed between modules before coding.
