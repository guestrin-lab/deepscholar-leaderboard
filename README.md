# 🏆 DeepScholar-Bench Leaderboard

A comprehensive leaderboard for evaluating research AI systems across multiple dimensions of quality and accuracy.

## 📊 About DeepScholar-Bench

**DeepScholar-Bench** is a live benchmark for evaluating generative research synthesis systems. It draws queries from recent ArXiv papers and focuses on generating related work sections by retrieving, synthesizing, and citing prior research. The benchmark provides holistic automated evaluation across three key dimensions with metrics that show strong agreement with expert human judgments.

## 🔬 Evaluation Metrics

The benchmark evaluates systems across three main categories:

### 🧠 Knowledge Synthesis
- **Organization (Org.)**: Assesses organization and coherence of system answer
- **Nugget Coverage (Nugget Cov.)**: Assesses the answer's coverage of essential facts

### 🔍 Retrieval Quality
- **Relevance Rate (Rel. Rate.)**: Measures avg. relevance among all referenced sources
- **Document Importance (Doc. Imp.)**: Measures how notable referenced sources are, using citation counts
- **Reference Coverage (Ref. Cov.)**: Assesses the referenced set's coverage of key, important references

### ✅ Verifiability
- **Citation Precision (Cite-P)**: Measures percent of cited sources that support their accompanying claim
- **Claim Coverage (Claim Cov.)**: Measures percent of claims that are fully supported by cited sources

## 🚀 Live Leaderboard

The live leaderboard is hosted on GitHub Pages and can be accessed at:
**https://guestrin-lab.github.io/deepscholar-leaderboard/**

## 📁 Repository Structure

```
deepscholar-bench/
├── deepscholar_bench_leaderboard.html  # Main leaderboard HTML file
├── leaderboard_data.csv                 # CSV data for the leaderboard
├── create_leaderboard.py               # Python script to generate the leaderboard
└── README.md                           # This file
```

## 🔄 Updating the Leaderboard

To update the leaderboard with new data:

1. Run the Python script:
   ```bash
   python create_leaderboard.py
   ```

2. The script will:
   - Fetch the latest data from Google Sheets
   - Process and clean the data
   - Generate an updated HTML leaderboard
   - Save both HTML and CSV versions

3. Commit and push the changes to trigger a GitHub Pages update

## 🌐 GitHub Pages Setup

This repository is configured to host the leaderboard on GitHub Pages. The main HTML file (`deepscholar_bench_leaderboard.html`) will be automatically served at the repository's GitHub Pages URL.

## 📊 Current Top Performers

The leaderboard currently shows the top research AI systems ranked by their average performance across all metrics. Systems are categorized as either "Open" (open-source) or "Closed" (proprietary) and include information about the underlying language models used.

## 🤝 Contributing

To submit your solution to the DeepScholar-Bench leaderboard:

1. Use our [Google Form](https://docs.google.com/forms/d/e/1FAIpQLSeug4igDHhVUU3XnrUSeMVRUJFKlHP28i8fcBAu_LHCkqdV1g/viewform?usp=dialog) to submit your results
2. Provide details about your system architecture and methodology
3. Submit your results for evaluation

For questions and inquiries, please contact: lianapat@stanford.edu

## 📚 References

- **GitHub Repository**: [https://github.com/guestrin-lab/deepscholar-bench](https://github.com/guestrin-lab/deepscholar-bench)
- **Research Paper**: [Link to be added]

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

*Last updated: 2025-01-26*
