const signedYear = (year, era) => {
  const value = Number.parseInt(year, 10);
  if (!Number.isInteger(value) || value < 1) return null;
  return era === "BCE" ? -value : value;
};

const displayYear = (signedValue) => {
  const year = Number.parseInt(signedValue, 10);
  if (!Number.isInteger(year) || year === 0) return null;
  return `${Math.abs(year)} ${year < 0 ? "BCE" : "CE"}`;
};

export { displayYear, signedYear };
