use pyo3::prelude::*;

#[pyclass]
pub enum IdentityTypes {
    Anonymous_PKI,
}


#[pyfunction]
pub fn configure_identity(identity_type: IdentityTypes) -> PyResult<String> {
    eprintln!("TODO implement configure_identity when given {:#?}", identity_type);
    Ok("Done!".into())
}



