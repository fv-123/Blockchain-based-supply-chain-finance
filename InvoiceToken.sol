// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "https://raw.githubusercontent.com/OpenZeppelin/openzeppelin-contracts/v4.8.0/contracts/token/ERC721/ERC721.sol";
import "https://raw.githubusercontent.com/OpenZeppelin/openzeppelin-contracts/v4.8.0/contracts/access/Ownable.sol";
import "https://raw.githubusercontent.com/OpenZeppelin/openzeppelin-contracts/v4.8.0/contracts/utils/Counters.sol";

contract InvoiceToken is ERC721, Ownable {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIds;

    enum InvoiceStatus { Issued, Financed, Settled }

    struct Invoice {
        uint256 amount;
        uint256 dueDate;
        address supplier;
        address debtor;
        InvoiceStatus status;
        string metadataURI;
    }

    mapping(uint256 => Invoice) public invoices;
    mapping(address => bool) public authorizedSuppliers;
    mapping(address => bool) public authorizedFinanciers;

    event InvoiceIssued(uint256 indexed invoiceId, address indexed supplier);
    event InvoiceFinanced(uint256 indexed invoiceId, address indexed financier);
    event InvoiceSettled(uint256 indexed invoiceId);

    constructor() ERC721("InvoiceToken", "INVOICE") {}

    function authorizeSupplier(address supplier, bool allowed) external onlyOwner {
        authorizedSuppliers[supplier] = allowed;
    }

    function authorizeFinancier(address financier, bool allowed) external onlyOwner {
        authorizedFinanciers[financier] = allowed;
    }

    function mintInvoice(address debtor, uint256 amount, uint256 dueDate, string calldata metadataURI) external returns (uint256) {
        require(authorizedSuppliers[msg.sender], "Not authorized supplier");
        require(amount > 0, "Amount>0");
        require(dueDate > block.timestamp, "dueDate must be future");

        _tokenIds.increment();
        uint256 newId = _tokenIds.current();
        _safeMint(msg.sender, newId);

        invoices[newId] = Invoice({
            amount: amount,
            dueDate: dueDate,
            supplier: msg.sender,
            debtor: debtor,
            status: InvoiceStatus.Issued,
            metadataURI: metadataURI
        });

        emit InvoiceIssued(newId, msg.sender);
        return newId;
    }

    function transferToFinancier(uint256 invoiceId, address financier) external {
        require(authorizedFinanciers[financier], "Financier not authorized");
        require(ownerOf(invoiceId) == msg.sender, "Only owner can transfer");
        require(invoices[invoiceId].status == InvoiceStatus.Issued, "Invoice not issued");

        _transfer(msg.sender, financier, invoiceId);
        invoices[invoiceId].status = InvoiceStatus.Financed;
        emit InvoiceFinanced(invoiceId, financier);
    }

    function markSettled(uint256 invoiceId) external onlyOwner {
        require(invoices[invoiceId].status == InvoiceStatus.Financed || invoices[invoiceId].status == InvoiceStatus.Issued, "Wrong status");
        invoices[invoiceId].status = InvoiceStatus.Settled;
        emit InvoiceSettled(invoiceId);
    }

    function getInvoice(uint256 invoiceId) external view returns (
        uint256 amount, uint256 dueDate, address supplier, address debtor, InvoiceStatus status, string memory metadataURI
    ) {
        Invoice storage inv = invoices[invoiceId];
        return (inv.amount, inv.dueDate, inv.supplier, inv.debtor, inv.status, inv.metadataURI);
    }
}
