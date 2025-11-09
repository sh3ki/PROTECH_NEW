/**
 * Reusable Pagination Component
 * Provides pagination functionality for admin tables
 */
class PaginationComponent {
    constructor(options) {
        this.containerId = options.containerId || 'pagination-container';
        this.fetchFunction = options.fetchFunction; // Function to call when page changes
        this.currentPage = 1;
        this.itemsPerPage = options.itemsPerPage || 10;
        
        this.container = document.getElementById(this.containerId);
        if (!this.container) {
            console.error(`Pagination container with id '${this.containerId}' not found`);
            return;
        }
        
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        // Items per page change handler
        const itemsPerPageSelect = this.container.querySelector('.items-per-page-select');
        if (itemsPerPageSelect) {
            itemsPerPageSelect.addEventListener('change', (e) => {
                this.itemsPerPage = parseInt(e.target.value);
                this.currentPage = 1; // Reset to first page
                if (this.fetchFunction) {
                    this.fetchFunction(this.currentPage, this.itemsPerPage);
                }
            });
        }
    }
    
    update(paginationData) {
        if (!this.container) return;
        
        const {
            current_page,
            num_pages,
            has_next,
            has_previous,
            page_range,
            start_index,
            end_index,
            total_count
        } = paginationData;
        
        this.currentPage = current_page;
        
        // Update results info
        this.updateResultsInfo(start_index, end_index, total_count);
        
        // Update pagination navigation
        this.updatePaginationNav(current_page, num_pages, has_next, has_previous, page_range);
        
        // Show/hide pagination container based on results
        if (total_count > 0) {
            this.container.classList.remove('hidden');
        } else {
            this.container.classList.add('hidden');
        }
    }
    
    updateResultsInfo(startIndex, endIndex, totalCount) {
        const startIndexSpan = this.container.querySelector('.start-index');
        const endIndexSpan = this.container.querySelector('.end-index');
        const totalCountSpan = this.container.querySelector('.total-count');
        
        if (startIndexSpan) startIndexSpan.textContent = startIndex || 0;
        if (endIndexSpan) endIndexSpan.textContent = endIndex || 0;
        if (totalCountSpan) totalCountSpan.textContent = totalCount || 0;
    }
    
    updatePaginationNav(currentPage, numPages, hasNext, hasPrevious, pageRange) {
        const firstPageBtn = this.container.querySelector('.first-page-btn');
        const prevPageBtn = this.container.querySelector('.prev-page-btn');
        const nextPageBtn = this.container.querySelector('.next-page-btn');
        const lastPageBtn = this.container.querySelector('.last-page-btn');
        const pageNumbersContainer = this.container.querySelector('.page-numbers');
        
        // Update first page button
        if (firstPageBtn) {
            firstPageBtn.disabled = !hasPrevious || currentPage === 1;
            firstPageBtn.onclick = () => {
                if (!firstPageBtn.disabled && this.fetchFunction) {
                    this.fetchFunction(1, this.itemsPerPage);
                }
            };
        }
        
        // Update previous page button
        if (prevPageBtn) {
            prevPageBtn.disabled = !hasPrevious;
            prevPageBtn.onclick = () => {
                if (!prevPageBtn.disabled && this.fetchFunction) {
                    this.fetchFunction(currentPage - 1, this.itemsPerPage);
                }
            };
        }
        
        // Update next page button
        if (nextPageBtn) {
            nextPageBtn.disabled = !hasNext;
            nextPageBtn.onclick = () => {
                if (!nextPageBtn.disabled && this.fetchFunction) {
                    this.fetchFunction(currentPage + 1, this.itemsPerPage);
                }
            };
        }
        
        // Update last page button
        if (lastPageBtn) {
            lastPageBtn.disabled = !hasNext || currentPage === numPages;
            lastPageBtn.onclick = () => {
                if (!lastPageBtn.disabled && this.fetchFunction) {
                    this.fetchFunction(numPages, this.itemsPerPage);
                }
            };
        }
        
        // Update page numbers
        if (pageNumbersContainer && pageRange) {
            let pageNumbersHtml = '';
            
            pageRange.forEach(pageNum => {
                if (pageNum === currentPage) {
                    pageNumbersHtml += `
                        <span class="relative inline-flex items-center px-4 py-2 border border-primary dark:border-tertiary bg-primary dark:bg-tertiary text-sm font-medium text-white">
                            ${pageNum}
                        </span>`;
                } else {
                    pageNumbersHtml += `
                        <button class="page-number-btn relative inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors" 
                                data-page="${pageNum}">
                            ${pageNum}
                        </button>`;
                }
            });
            
            pageNumbersContainer.innerHTML = pageNumbersHtml;
            
            // Add event listeners to page number buttons
            pageNumbersContainer.querySelectorAll('.page-number-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    const pageNum = parseInt(btn.dataset.page);
                    if (this.fetchFunction) {
                        this.fetchFunction(pageNum, this.itemsPerPage);
                    }
                });
            });
        }
    }
    
    // Method to set items per page programmatically
    setItemsPerPage(itemsPerPage) {
        this.itemsPerPage = itemsPerPage;
        const select = this.container.querySelector('.items-per-page-select');
        if (select) {
            select.value = itemsPerPage;
        }
    }
    
    // Method to get current items per page
    getItemsPerPage() {
        return this.itemsPerPage;
    }
    
    // Method to get current page
    getCurrentPage() {
        return this.currentPage;
    }
    
    // Method to hide pagination
    hide() {
        if (this.container) {
            this.container.classList.add('hidden');
        }
    }
    
    // Method to show pagination
    show() {
        if (this.container) {
            this.container.classList.remove('hidden');
        }
    }
}