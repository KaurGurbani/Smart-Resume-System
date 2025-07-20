import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def score_resumes(job_description):
    try:
        df = pd.read_excel("resume_data.xlsx")
        print("Resume Data Read Successfully:")
        print(df.head())  # 👈 Debug print

        if df.empty:
            print("❌ DataFrame is empty!")
            return []

        # Combine relevant fields into a string for each resume
        df["combined"] = df[["Name", "Skills", "Experience", "Education"]].fillna("").agg(" ".join, axis=1)

        # Include job description in TF-IDF vectorizer
        corpus = [job_description] + df["combined"].tolist()

        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(corpus)

        # Compare JD to each resume
        similarity_scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

        df["score"] = similarity_scores
        df = df.sort_values(by="score", ascending=False)

        results = df[["Name", "score"]].reset_index(drop=True)
        print("✅ Final Scored Data:")
        print(results)  # 👈 Debug print

        return results.to_dict(orient="records")

    except Exception as e:
        print(f"🔥 Error in scoring resumes: {e}")
        return []
