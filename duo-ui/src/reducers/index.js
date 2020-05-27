import { combineReducers } from 'redux';
import dataReducer from './dataReducer';
import authReducer from './authReducer';

const reducer = combineReducers({
  authReducer,
  dataReducer,
});

export default reducer;
