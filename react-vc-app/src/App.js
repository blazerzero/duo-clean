import React, { Component } from 'react';
import { PersistGate } from 'redux-persist/integration/react';
import { Provider } from 'react-redux';
import { BrowserRouter as Router, Route, Link } from 'react-router-dom';
import logo from './images/logo.svg';
import { store, persistor } from './store.js';
import './css/App.css';

import Header from './fragments/Header';
import Import from './screens/Import';
import Results from './screens/Results';

class App extends Component {
  render() {
    return (
      <Provider store={store}>
        <PersistGate loading={null} persistor={persistor}>
          <Router>
            {/*<div>
              <Header />
            </div>*/}

            <Route path='/' exact component={Import} />
            <Route path='/results/' component={Results} />
          </Router>
        </PersistGate>
      </Provider>
    );
  }
}

export default App;

/*function App() {
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>
          Edit <code>src/App.js</code> and save to reload.
        </p>
        <a
          className="App-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
          Learn React
        </a>
      </header>
    </div>
  );
}

export default App;*/
