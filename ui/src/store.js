import { createStore, applyMiddleware } from 'redux';
import { createLogger } from 'redux-logger';
import { persistStore, persistReducer } from 'redux-persist';
import storage from 'redux-persist/lib/storage';

import reducer from './reducers';

const persistConfig = {
  key: 'root',
  storage: storage,
  whitelist: [
    'importReducer',
  ],
};

const persistedReducer = persistReducer(persistConfig, reducer);

const store = createStore(persistedReducer);
let persistor = persistStore(store);

export {
  store,
  persistor,
};
