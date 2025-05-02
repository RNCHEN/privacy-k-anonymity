# K-Anonymity Privacy Project

This project focuses on achieving **K-Anonymity** for sensitive datasets using the [ARX anonymization tool](https://arx.deidentifier.org/), along with custom metrics and evaluation scripts.

## 📁 Project Structure

```
projext/
├── code/
│   ├── java/                  # Java source code
│   ├── kanonymity/            # Main Java module implementing k-anonymity
│   ├── arx-3.9.1-win-64.jar   # ARX anonymization toolkit (local JAR)
│   └── own_metrics.ipynb      # Jupyter notebook for custom metric analysis
├── reference/                 # Reference materials and external sources
├── Scientific Poster/         # Presentation materials and report graphics
├── Final Report.pdf           # Final project report
├── 17735_Group1_Achieving k-Anonymity_ProjectDescription.pdf
└── readme.md                  # You are here
```

## 🛠️ Getting Started

1. Make sure you have **Java 17+** and **Maven** installed.
2. Compile the Java project:

   ```bash
   cd code/kanonymity
   mvn clean compile
   ```
3. If the dataset is missing or unavailable, please download it from [this source](https://healthdata.gov/Health/COVID-19-Public-Therapeutic-Locator/rxn6-qnx8/about_data).

4. Run the program:

   ```bash
   mvn exec:java -Dexec.mainClass="org.example.App"
   ```

   > If `arx-3.9.1-win-64.jar` is not in your local Maven repository, install it manually:
   >
   > ```bash
   > mvn install:install-file ^
   > -Dfile=arx-3.9.1-win-64.jar ^
   > -DgroupId=org.deidentifier ^
   > -DartifactId=arx ^
   > -Dversion=3.9.1 ^
   > -Dpackaging=jar
   > 
   > OR
   > 
   > Check the official download insrtuction here https://arx.deidentifier.org/downloads/
   > ```

## 📊 Notebooks

- `own_metrics.ipynb`: Custom evaluation metrics for analyzing anonymized outputs, built in Python.

## 📚 Poster and Report

- Posters are located in the `Scientific Poster/` folder.
- report is in root folder. 

## ✅ Project Goals

- Apply K-Anonymity to real-world datasets
- Evaluate privacy and utility trade-offs using DM, AECS, and NCP
- Design and test custom risk metrics via Python notebook

## 🔗 Connection

If you have any questions regarding the project, feel free to reach out via email.  
📧 Email: [rnchen0218@gmail.com](mailto:rnchen0218@gmail.com)  
I typically respond within **one** business day.
