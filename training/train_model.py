import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
from pathlib import Path
import argparse
import re


def clean_text_simple(text: str) -> str:
    if not text:
        return ''
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'http\S+|www\S+', ' ', text)
    text = re.sub(r'[^A-Za-z0-9\s]', ' ', text)
    return text.lower()


def load_dataset(path: Path):
    return pd.read_csv(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', default='training/dataset.csv')
    parser.add_argument('--out-model', default='backend/model/spam_model.pkl')
    parser.add_argument('--out-vectorizer', default='backend/model/vectorizer.pkl')
    args = parser.parse_args()
    df = load_dataset(Path(args.dataset))
    df = df.dropna()
    X = df['text'].astype(str).apply(clean_text_simple)
    y = df['label'].astype(str)
    vect = TfidfVectorizer(max_features=5000)
    Xv = vect.fit_transform(X)
    Xtr, Xte, ytr, yte = train_test_split(Xv, y, test_size=0.2, random_state=42)
    clf = LogisticRegression(max_iter=1000)
    clf.fit(Xtr, ytr)
    preds = clf.predict(Xte)
    print(classification_report(yte, preds))
    print('Confusion matrix:\n', confusion_matrix(yte, preds))
    out_model = Path(args.out_model)
    out_vectorizer = Path(args.out_vectorizer)
    out_model.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, out_model)
    joblib.dump(vect, out_vectorizer)
    print(f'Model saved to {out_model}, vectorizer saved to {out_vectorizer}')


if __name__ == '__main__':
    main()
