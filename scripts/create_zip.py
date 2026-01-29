import zipfile
import os

def create_zip():
    source = r"C:\proyectos_dev\UTM\temp_test\Dim_Customers.sql"
    destination = r"C:\proyectos_dev\UTM\Dim_Customers_test.zip"
    
    if not os.path.exists(source):
        print(f"Error: Source {source} does not exist.")
        return

    try:
        with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(source, arcname="Dim_Customers.sql")
        
        if os.path.exists(destination):
            print(f"Successfully created {destination}")
            print(f"File size: {os.path.getsize(destination)} bytes")
        else:
            print(f"ERROR: File {destination} was NOT created.")
            
    except Exception as e:
        print(f"Error creating zip: {e}")

if __name__ == "__main__":
    create_zip()
