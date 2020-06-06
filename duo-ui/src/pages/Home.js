import React, { Component } from 'react';
import Welcome from '../components/Welcome';
import Import from '../components/Import';
import Header from '../components/Header';
import {
    Button,
    Row,
    Col
} from 'react-bootstrap';

export default class Home extends Component {

    constructor(props) {
        super(props);

        this.state = {
            importClicked: false
        }
    }

    _handleImportClick = () => {
        this.setState({ importClicked: true });
    }

    render() {
        return (
            <div className='content-centered site-page home'>
                <Header projectId='TBD'/>
                <Welcome />
                <br/>
                <Button size='lg' className='duo-btn round bvr-orange box-blur' onClick={this._handleImportClick}>IMPORT DATA</Button>
                {this.state.importClicked && <Import />}
            </div>
        );
    }
}