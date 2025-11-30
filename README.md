# Team Contribution Guide (Taglish Version) 🇵🇭

Hello team! Eto yung guide para di tayo magkagulo sa Git. Basahin niyo to please para smooth ang coding natin.

## ⚠️ SUPER IMPORTANT RULE
**Wag na wag kayong mag-cocommit directly sa `main` or `master` branch.** 
Doon lang tayo gagalaw sa assigned branches natin para di masira yung working code.

## 🚀 Paano Magsimula?

### 1. Download niyo muna yung Repo
Kung wala pa sa laptop niyo yung project, i-clone niyo muna.
```bash
git clone https://github.com/Sedictt/Finance-Tracker---Python.git
cd Finance-Tracker---Python
```

### 2. Lipat kayo sa Branch niyo
Bago kayo mag-start mag-code, siguraduhin niyong nasa tamang branch kayo. Bawal mag-code sa `main`!

*   **Margaux (@Margaux Delaog)**:
    ```bash
    git checkout Dashboard
    ```
*   **Mark (@Mark Roniel Dolot)**:
    ```bash
    git checkout Transaction
    ```
*   **Sean (@Sean Mark Vasquez)**:
    ```bash
    git checkout Analytics
    ```
*   **Jv (@Jv Tillo)**:
    ```bash
    git checkout Predictions
    # Or pag mag-aayos ka na:
    git checkout Polishing
    ```

### 3. Code na!
Gawin niyo na yung tasks niyo. Since nasa sarili kayong branch, safe yan. Kahit magkamali kayo, di madadamay yung gawa ng iba.

### 4. I-save ang gawa (Commit)
Pag may natapos kayong part (example: "tapos na yung login button" or "fixed yung bug"), i-save niyo na.
```bash
git add .
git commit -m "Lagay niyo dito kung ano ginawa niyo"
```
*Tip: Gawing clear yung message para alam namin kung para san yung code.*

### 5. I-upload ang gawa (Push)
Para makita namin yung progress at ma-save sa GitHub, i-push niyo.
```bash
git push origin <your-branch-name>
# Example: git push origin Dashboard
```

## 🤝 Pag tapos na kayo (Merging)

Pag tapos na talaga kayo sa feature niyo at confident na kayo na working siya:

1.  Punta kayo sa GitHub repo natin.
2.  May makikita kayong button na **"Compare & pull request"**. Click niyo yun.
3.  Check niyo yung changes kung tama, then click **"Create Pull Request"**.
4.  Chat niyo ko (Jv) para ma-review at ma-merge ko sa `main`.

## 🛡️ Tips para iwas sakit ulo

1.  **Focus lang sa files niyo.** Kung naka-assign ka sa Dashboard, try mong wag galawin yung files ng Transaction para walang conflict.
2.  **Update kayo palagi.** Kung may na-merge na bago sa `main` (example: tapos na si Mark), kunin niyo yung updates para fresh yung code niyo.
    ```bash
    git checkout main
    git pull origin main
    git checkout <your-branch>
    git merge main
    ```
3.  **Communication is key.** Pag may babaguhin kayong shared file (like database config), magsabi muna sa GC.

## 🆘 Help, may Error!

*   **"Merge Conflict"**: Nangyayari to pag dalawang tao ang nag-edit sa same line ng code. Wag mag-panic. Basahin niyo lang yung file, piliin kung alin yung tamang code, save, at commit ulit.
*   Pag di niyo na alam gagawin, chat niyo ko agad.

Happy coding guys! 🚀
