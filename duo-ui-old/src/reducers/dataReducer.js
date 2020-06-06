const initialState = {
  importedFile: null,
};

const importReducer = (state = initialState, action) => {
  switch (action.type) {
    case 'IMPORT_FILE': {
      return state;
    }
    default: {
      return state;
    }
  }
};

export default importReducer;
