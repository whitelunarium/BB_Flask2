import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier


class TitanicModel:
    """Singleton Titanic survival model backed by the seaborn dataset."""

    _instance = None

    def __init__(self):
        self.model = None
        self.dt = None
        self.features = ["pclass", "sex", "age", "sibsp", "parch", "fare", "alone"]
        self.target = "survived"
        self.titanic_data = sns.load_dataset("titanic")
        self.encoder = OneHotEncoder(handle_unknown="ignore")

    def _clean(self):
        self.titanic_data.drop(
            ["alive", "who", "adult_male", "class", "embark_town", "deck"],
            axis=1,
            inplace=True,
        )

        self.titanic_data["sex"] = self.titanic_data["sex"].apply(
            lambda value: 1 if value == "male" else 0
        )
        self.titanic_data["alone"] = self.titanic_data["alone"].apply(
            lambda value: 1 if value is True else 0
        )

        self.titanic_data.dropna(subset=["embarked"], inplace=True)

        onehot = self.encoder.fit_transform(self.titanic_data[["embarked"]]).toarray()
        cols = [f"embarked_{value}" for value in self.encoder.categories_[0]]
        onehot_df = pd.DataFrame(onehot, columns=cols, index=self.titanic_data.index)
        self.titanic_data = pd.concat([self.titanic_data, onehot_df], axis=1)
        self.titanic_data.drop(["embarked"], axis=1, inplace=True)
        self.features.extend(cols)

        self.titanic_data.dropna(inplace=True)

    def _train(self):
        x = self.titanic_data[self.features]
        y = self.titanic_data[self.target]

        self.model = LogisticRegression(max_iter=1000)
        self.model.fit(x, y)

        self.dt = DecisionTreeClassifier()
        self.dt.fit(x, y)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._clean()
            cls._instance._train()
        return cls._instance

    def predict(self, passenger):
        passenger_df = pd.DataFrame([passenger]).copy()
        passenger_df["sex"] = passenger_df["sex"].apply(
            lambda value: 1 if value == "male" else 0
        )
        passenger_df["alone"] = passenger_df["alone"].apply(
            lambda value: 1 if value is True else 0
        )

        onehot = self.encoder.transform(passenger_df[["embarked"]]).toarray()
        cols = [f"embarked_{value}" for value in self.encoder.categories_[0]]
        onehot_df = pd.DataFrame(onehot, columns=cols, index=passenger_df.index)
        passenger_df = pd.concat([passenger_df, onehot_df], axis=1)
        passenger_df.drop(["embarked", "name"], axis=1, inplace=True, errors="ignore")

        for feature in self.features:
            if feature not in passenger_df:
                passenger_df[feature] = 0

        passenger_df = passenger_df[self.features]
        die, survive = np.squeeze(self.model.predict_proba(passenger_df))
        return {"die": float(die), "survive": float(survive)}


def initTitanic():
    TitanicModel.get_instance()
