const initialState = {
  loggedIn: false,
};

const authReducer = (state = initialState, action) => {
  switch (action.type) {
    case 'LOGGED_IN': {
      return {
        ...state,
        email: action.payload.email,
        firstname: action.payload.firstname,
        lastname: action.payload.firstname,
      }
    }

    default: {
      return state;
    }
  }
};

export default authReducer;
