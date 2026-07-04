export function MeetingForm({
  customer,
  setCustomer,
  meetingType,
  setMeetingType,
  product,
  setProduct,
  deliverable,
  setDeliverable,
  notes,
  setNotes,
  customers,
  meetingTypes,
  products,
  deliverables,
  onGenerate,
  loading,
}) {
  return (
    <section className="panel">
      <h2>Meeting Context</h2>

      <label>
        Customer
        <select value={customer} onChange={(e) => setCustomer(e.target.value)}>
          {customers.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>
      </label>

      <label>
        Meeting Type
        <select value={meetingType} onChange={(e) => setMeetingType(e.target.value)}>
          {meetingTypes.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </label>

      <label>
        Product
        <select value={product} onChange={(e) => setProduct(e.target.value)}>
          {products.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </label>

      <label>
        Deliverable Format
        <select value={deliverable} onChange={(e) => setDeliverable(e.target.value)}>
          {deliverables.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </label>

      <label>
        Additional Notes / Context
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="e.g., Recent customer projects, focus areas, or special requests"
          rows="4"
        />
      </label>

      <button onClick={onGenerate} disabled={loading}>
        {loading ? 'Generating...' : 'Generate Brief'}
      </button>
    </section>
  )
}
