"""Optional: pre-train the cancellation-risk model so the app starts instantly.

    python train_model.py
"""
from modules import data_loader, model, settings

if __name__ == "__main__":
    rate = float(settings.load()["eur_to_inr"])
    df = data_loader.load_all(rate)
    bundle = model.train(df)
    m = bundle["metrics"]
    print(f"Trained on {bundle['n_rows']:,} rows | accuracy {m['accuracy']:.3f} | AUC {m['auc']:.3f}")
    print("Saved to models/cancel_model.joblib")
