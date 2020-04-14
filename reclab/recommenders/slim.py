"""An implementation of the SLIM recommender.

See http://glaros.dtc.umn.edu/gkhome/node/774 for details.
"""
import numpy as np
import scipy.sparse

from . import recommender


class SLIM(recommender.PredictRecommender):
    """The SLIM recommendation model which is a sparse linear method.

    Parameters
    ----------
    alpha : float
        Constant that multiplies the regularization terms.
    l1_ratio : float
        The ratio of the L1 regularization term with respect to the L2 regularization.
    max_iter : int
        The maximum number of iterations to train the model for.
    tol : float
        The tolerance below which the optimization will stop.
    seed : int
        The random seed to use when training the model.

    """

    def __init__(self,
                 alpha=1.0,
                 l1_ratio=0.1,
                 positive=True,
                 max_iter=100,
                 tol=1e-4,
                 seed=0):
        """Create a SLIM recommender."""
        self._model = ElasticNet(alpha=alpha,
                                 l1_ratio=l1_ratio,
                                 positive=positive,
                                 fit_intercept=False,
                                 copy_X=False,
                                 precompute=True,
                                 selection='random',
                                 max_iter=max_iter,
                                 tol=tol,
                                 random_state=seed)
        self._weights = None
        super().__init__()

    def update(self, users=None, items=None, ratings=None):  # noqa: D102
        super().update(users, items, ratings)
        num_items = len(self._items)
        self._weights = scipy.sparse.dok_matrix((num_items, num_items))
        ratings = self._ratings.tocsc()
        for item_id in range(num_items):
            target = ratings[:, item_id].toarray()
            # Zero out the column of the current item to prevent a trivial solution.
            ratings[:, item_id] = 0
            # Fit the mode and save the weights
            self.model.fit(ratings, target)
            self._weights[:, item_id] = self.model.sparse_coef_
            self._weights[item_id, item_id] = 0
            # Restore the rating column.
            ratings[:, item_id] = target
        self._weights = self._weights.tocsr()

    def _predict(self, user_item):  # noqa: D102
        # Predict on all user-item pairs.
        all_predictions = self._ratings @ self._weights
        predictions = []
        for (user_id, item_id), _ in user_item:
            predictions.append(all_predictions[user_id, item_id])

        return np.array(predictions)
