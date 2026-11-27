# Privacy

0. **The contract, stated in this exact wording in the README (before the menu) and in this rule:** "Your source never leaves your machine except to the model provider your agent host already uses; the tool adds no network calls, no telemetry and no uploads."
1. Local and private sources are **snapshotted** into `runs/<id>/target/` (option 1 copies the folder, option 2 clones the repository). The run is then immune to edits of, or moves of, the original folder. The snapshot is git-ignored and never copied into `baseline/`, `reports/` (except as relative citations), or any commit.
2. Credentials are handled only by the user's git (credential helper, SSH agent). The tool never asks for, stores or logs a token. `intake` refuses URLs that embed credentials (`https://user:token@…`) with exit 2 and tells the user to use a credential helper.
3. **No telemetry.** The engine makes network calls in exactly two commands:
   - `engine fetch`: git clone/fetch of registry URLs, registry docs URLs, and the tokenizer file;
   - `engine intake --mode git`: a clone of the URL the user gave, with the user's own git.

   `--offline` (or `AMA_OFFLINE=1`) makes both exit 6 instead of touching the network.
4. **Footer restatement.** The report footer repeats the contract sentence from rule 0. Owner decision D13 accepts this wording as the interpretation of "private sources never leave the machine".
5. A report that includes a private target carries a "Private: contains the assessment of a private target" banner. `engine report --public` refuses to render private targets (exit 1).
6. Names of people, emails and handles found in documentation-only inputs are omitted from every output.
