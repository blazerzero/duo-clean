import React, { Component } from 'react';
import BootstrapTable from 'react-bootstrap-table-next';
import {
  Table as RBTable,
  Row,
  Col
} from 'react-bootstrap';

export default class Table extends Component {
    
    constructor(props) {
        super(props);
        this.state = {
            header: this.props.header,
        }
    }

    render() {
        /* const products = [];
        const columns = [{
            dataField: 'id',
            text: 'Product ID'
        }, {
            dataField: 'name',
            text: 'Product Name'
        }, {
            dataField: 'price',
            text: 'Product Price'
        }]; */
        return (
          <RBTable bordered responsive>
            <thead>
              <tr>
                <th>Noisy Tuple?</th>
                {  }
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>
                  
                </td>
              </tr>
            </tbody>
          </RBTable>
        )
    }
}
