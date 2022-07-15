def dfget(df, column, **kwargs):
    """
    Get a single cell value from a table.

    Parameters
    ----------
    df : data frame
        
    column : column to get a cell from
        
    **kwargs : columns names and values to filter rows
        

    Returns
    -------
    scalar
    """
    for key, val in kwargs.items():
        df = df[df[key] == val]
    return df[column].values[0]
