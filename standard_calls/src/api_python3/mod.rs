use pyo3::prelude::*;

#[pyclass]
pub enum IdentityTypes {
    Anonymous_PKI,
}


#[pyfunction]
pub fn configure_identity(identity_type: usize) -> PyResult<String> {
    eprintln!("TODO implement configure_identity when given {:#?}", identity_type);
    Ok("Done!".into())
}


#[pymodule(name="standard_calls")]
pub fn standard_calls(m: &Bound<'_, PyModule>) -> PyResult<()> {
    eprintln!("Began adding things!");
    m.add_function(wrap_pyfunction!(configure_identity, m)?)?;
    m.add_class::<IdentityTypes>()?;
    eprintln!("Done adding things!");
    Ok(())
}


