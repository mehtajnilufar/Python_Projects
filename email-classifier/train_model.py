# train_model.py
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import argparse


def load_data(csv_path):
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=['text', 'label'])
    return df['text'].astype(str), df['label'].astype(str)


def build_pipeline():
    vec = TfidfVectorizer(stop_words="english")
    clf = MultinomialNB()
    pipe = Pipeline([
        ('tfidf', vec),
        ('clf', clf)
    ])
    return pipe


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", default="models/email_classifier.joblib")
    args = parser.parse_args()

    X, y = load_data(args.data)

    # SIMPLE SPLIT (NO STRATIFY → NO ERROR)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    pipe = build_pipeline()
    pipe.fit(X_train, y_train)

    preds = pipe.predict(X_test)
    print(classification_report(y_test, preds))

    joblib.dump(pipe, args.out)
    print(f"Model saved to {args.out}")


if __name__ == "__main__":
    main()
