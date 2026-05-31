const state = {
  products: [],
  filteredProducts: []
};

const elements = {
  totalProducts: document.querySelector('#totalProducts'),
  newLaunches: document.querySelector('#newLaunches'),
  afProducts: document.querySelector('#afProducts'),
  mfProducts: document.querySelector('#mfProducts'),
  linkedProducts: document.querySelector('#linkedProducts'),
  searchInput: document.querySelector('#searchInput'),
  focusFilter: document.querySelector('#focusFilter'),
  mountFilter: document.querySelector('#mountFilter'),
  formatFilter: document.querySelector('#formatFilter'),
  statusFilter: document.querySelector('#statusFilter'),
  newLaunchesGrid: document.querySelector('#newLaunchesGrid'),
  productGrid: document.querySelector('#productGrid'),
  noLaunches: document.querySelector('#noLaunches'),
  noProducts: document.querySelector('#noProducts'),
  productDialog: document.querySelector('#productDialog'),
  dialogContent: document.querySelector('#dialogContent'),
  dialogClose: document.querySelector('.dialog-close')
};

function normalizeProductName(value = '') {
  return value
    .toString()
    .normalize('NFKC')
    .replace(/Ⅱ/g, 'II')
    .replace(/Ⅲ/g, 'III')
    .replace(/Ⅳ/g, 'IV')
    .replace(/full\s*-?\s*frame/gi, 'fullframe')
    .replace(/aps\s*-?\s*c/gi, 'apsc')
    .replace(/\b(AF|MF)(?=\d)/gi, '$1 ')
    .replace(/(\d+mm)(F\d)/gi, '$1 $2')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
}

function hasAssetLinks(product) {
  return Array.isArray(product.assetLinks) && product.assetLinks.some((link) => link.url && link.url.trim());
}

function displayValue(value) {
  return value && value.toString().trim() ? value : '—';
}

function getPrimaryAsset(product) {
  return (product.assetLinks || []).find((link) => link.url && link.url.trim());
}

function isNewLaunch(product) {
  return product.isNewLaunch || ['Coming Soon', 'Launching'].includes(product.status);
}

function compareLaunchDate(a, b) {
  const aDate = a.launchDate || '9999-12-31';
  const bDate = b.launchDate || '9999-12-31';
  return aDate.localeCompare(bDate) || a.productName.localeCompare(b.productName);
}

function updateDashboard(products) {
  elements.totalProducts.textContent = products.length;
  elements.newLaunches.textContent = products.filter(isNewLaunch).length;
  elements.afProducts.textContent = products.filter((product) => product.focusType === 'AF').length;
  elements.mfProducts.textContent = products.filter((product) => product.focusType === 'MF').length;
  elements.linkedProducts.textContent = products.filter(hasAssetLinks).length;
}

function productMatchesFilters(product) {
  const query = normalizeProductName(elements.searchInput.value);
  const focus = elements.focusFilter.value;
  const mount = elements.mountFilter.value;
  const format = elements.formatFilter.value;
  const status = elements.statusFilter.value;
  const searchable = normalizeProductName([
    product.productName,
    product.model,
    product.mount,
    product.format
  ].join(' '));

  return (!query || searchable.includes(query))
    && (focus === 'All' || product.focusType === focus)
    && (mount === 'All' || product.mount === mount)
    && (format === 'All' || product.format === format)
    && (status === 'All' || product.status === status);
}

function createProductCard(product) {
  const card = document.createElement('article');
  card.className = 'product-card';
  const asset = getPrimaryAsset(product);

  card.innerHTML = `
    <img src="${product.thumbnail || 'assets/thumbnails/placeholder.svg'}" alt="${product.productName} thumbnail">
    <div class="product-card__body">
      <div>
        <h3>${product.productName}</h3>
        <div class="badges">
          <span class="badge">${displayValue(product.focusType)}</span>
          <span class="badge">${displayValue(product.format)}</span>
          <span class="badge">${displayValue(product.status)}</span>
        </div>
      </div>
      <dl class="product-meta">
        <div><dt>Model</dt><dd>${displayValue(product.model)}</dd></div>
        <div><dt>Mount</dt><dd>${displayValue(product.mount)}</dd></div>
        <div><dt>Arrival Date</dt><dd>${displayValue(product.arrivalDate)}</dd></div>
        <div><dt>Launch Date</dt><dd>${displayValue(product.launchDate)}</dd></div>
        <div><dt>RRP</dt><dd>${displayValue(product.rrp)}</dd></div>
        <div><dt>Launch Price</dt><dd>${displayValue(product.launchPrice)}</dd></div>
      </dl>
      <div class="card-actions">
        <button type="button" data-action="details">View Details</button>
        ${asset ? `<a class="button primary-link" href="${asset.url}" target="_blank" rel="noopener">Open Asset Folder</a>` : '<span class="button button--disabled">Assets Coming Soon</span>'}
      </div>
    </div>
  `;

  card.querySelector('[data-action="details"]').addEventListener('click', () => openDetails(product));
  return card;
}

function renderProducts() {
  const filteredProducts = state.products.filter(productMatchesFilters);
  state.filteredProducts = filteredProducts;

  elements.productGrid.innerHTML = '';
  filteredProducts.forEach((product) => elements.productGrid.appendChild(createProductCard(product)));
  elements.noProducts.hidden = filteredProducts.length > 0;

  const launches = state.products.filter(isNewLaunch).sort(compareLaunchDate);
  elements.newLaunchesGrid.innerHTML = '';
  launches.forEach((product) => elements.newLaunchesGrid.appendChild(createProductCard(product)));
  elements.noLaunches.hidden = launches.length > 0;
}

function detailItems(items) {
  return `<div class="detail-grid">${items.map(([label, value]) => `
    <div class="detail-item"><span>${label}</span><strong>${displayValue(value)}</strong></div>
  `).join('')}</div>`;
}

function renderFeatures(product) {
  const en = product.keyFeatures?.en || [];
  const cn = product.keyFeatures?.cn || [];
  if (!en.length && !cn.length) {
    return '<p class="empty-state">Key features will be updated soon.</p>';
  }
  return `
    ${en.length ? `<h4>English</h4><ul class="feature-list">${en.map((item) => `<li>${item}</li>`).join('')}</ul>` : ''}
    ${cn.length ? `<h4>中文</h4><ul class="feature-list">${cn.map((item) => `<li>${item}</li>`).join('')}</ul>` : ''}
  `;
}

function specsAreIncomplete(product) {
  const values = Object.values(product.specs || {});
  return values.length === 0 || values.every((value) => !value || !value.toString().trim());
}

function buildInquiryUrl(product) {
  const subject = `Inquiry - Brightin Star ${product.productName}`;
  const body = [
    `Product Name: ${product.productName}`,
    `Model: ${product.model || ''}`,
    `Mount: ${product.mount || ''}`,
    'Message: I would like to know more about this product.'
  ].join('\n');
  return `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

function openDetails(product) {
  const asset = getPrimaryAsset(product);
  const specs = product.specs || {};
  const showIncompleteMessage = !product.isNewLaunch && specsAreIncomplete(product);

  elements.dialogContent.innerHTML = `
    <div class="dialog-inner">
      <div class="dialog-title">
        <p class="eyebrow">Product details</p>
        <h2>${product.productName}</h2>
      </div>

      <section class="detail-section">
        <h3>Product Information</h3>
        ${detailItems([
          ['Product Name', product.productName], ['Model', product.model], ['EAN', product.ean],
          ['Focus Type', product.focusType], ['Series', product.series], ['Mount', product.mount],
          ['Format', product.format], ['Color', product.color], ['Status', product.status]
        ])}
      </section>

      <section class="detail-section">
        <h3>Launch Information</h3>
        ${detailItems([
          ['Arrival Date', product.arrivalDate], ['Launch Date', product.launchDate], ['Launch Period', product.launchPeriod]
        ])}
      </section>

      <section class="detail-section">
        <h3>Public Pricing</h3>
        ${detailItems([['RRP', product.rrp], ['Launch Price', product.launchPrice]])}
      </section>

      <section class="detail-section">
        <h3>Specifications</h3>
        ${showIncompleteMessage ? '<p class="empty-state">Detailed specifications will be updated soon.</p>' : ''}
        ${detailItems([
          ['Product Material', specs.productMaterial], ['Product Dimensions', specs.productDimensions],
          ['Product Weight', specs.productWeight], ['Included Accessories', specs.includedAccessories],
          ['Manual', specs.manual], ['Angle of View', specs.angleOfView],
          ['Minimum Focus Distance', specs.minimumFocusDistance], ['Magnification', specs.magnification],
          ['Optical Design', specs.opticalDesign], ['Aperture', specs.aperture],
          ['Iris Blades', specs.irisBlades], ['Focus Type', specs.focusType],
          ['Image Stabilization', specs.imageStabilization], ['Filter Size', specs.filterSize],
          ['Weather Sealing', specs.weatherSealing], ['Buttons & Knobs Description', specs.buttonsAndKnobsDescription]
        ])}
      </section>

      <section class="detail-section">
        <h3>Key Features</h3>
        ${renderFeatures(product)}
      </section>

      <section class="detail-section">
        <h3>Download Assets</h3>
        ${asset ? `<a class="button primary-link" href="${asset.url}" target="_blank" rel="noopener">Open Asset Folder</a>` : '<p class="empty-state">Assets coming soon.</p>'}
      </section>

      <section class="detail-section">
        <h3>Inquiry</h3>
        <a class="button primary-link" href="${buildInquiryUrl(product)}">Email Inquiry</a>
      </section>
    </div>
  `;

  elements.productDialog.showModal();
}

async function loadProducts() {
  try {
    const response = await fetch('products.json');
    if (!response.ok) throw new Error(`Failed to load products.json: ${response.status}`);
    state.products = await response.json();
    updateDashboard(state.products);
    renderProducts();
  } catch (error) {
    elements.productGrid.innerHTML = `<p class="empty-state">${error.message}. Please preview this site with a local web server.</p>`;
  }
}

['input', 'change'].forEach((eventName) => {
  [elements.searchInput, elements.focusFilter, elements.mountFilter, elements.formatFilter, elements.statusFilter]
    .forEach((element) => element.addEventListener(eventName, renderProducts));
});

elements.dialogClose.addEventListener('click', () => elements.productDialog.close());
elements.productDialog.addEventListener('click', (event) => {
  if (event.target === elements.productDialog) elements.productDialog.close();
});

loadProducts();
